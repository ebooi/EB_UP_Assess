"""
What-If Scenarios page.

Three tabs:
1. Comprehensive Scenario Inputs (headcount/grad/research/debt/capacity/staff growth,
   penalty trigger, internal funding pool)
2. Shape and Size Simulator (postgraduate share, SET share)
3. Faculty and Funding Group disaggregation
"""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.calculations import calculate_subsidy_exposure
from utils.constants import (
    DHET_OVER_THRESHOLD, DHET_UNDER_THRESHOLD, RAND_PER_TIU_2026_27,
    REMOVAL_RATE_2024, REMOVAL_RATE_2025, REMOVAL_RATE_2026,
    UP_BLUE, UP_GOLD, UP_LIGHT_GREY, UP_RED,
)
from utils.data_loader import aggregate, load_enrolment_data
from utils.filters import apply_filters
from utils.forecasting import shape_size_simulation
from utils.theme import apply_theme, page_header

st.set_page_config(page_title="What-If Scenarios", layout="wide", page_icon="🎯")
apply_theme()
page_header(
    "What-If Scenarios",
    "Comprehensive scenario inputs, shape-and-size simulator, faculty and funding group view",
)

df_raw = load_enrolment_data()
df = apply_filters(df_raw)

if df.empty:
    st.warning("No data matches the current filters.")
    st.stop()

inst = aggregate(df, ["Year"])
fac = aggregate(df, ["Year", "Faculty", "FacultyCode"])
latest_year = int(df["Year"].max())
latest_inst = inst[inst["Year"] == latest_year].iloc[0]

tab1, tab2, tab3 = st.tabs([
    "Comprehensive Scenario",
    "Shape and Size Simulator",
    "Faculty and Funding Group View"
])

# ===========================================================================
# TAB 1 - COMPREHENSIVE SCENARIO
# ===========================================================================
with tab1:
    st.markdown(f"<h3 style='color:{UP_BLUE};'>Comprehensive scenario inputs</h3>", unsafe_allow_html=True)
    st.caption(
        "Set growth rates and policy parameters to see the combined impact across "
        "headcount, graduates, research, debt, capacity, staff, and funding adequacy."
    )

    # Two columns of inputs
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Growth assumptions</h4>", unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    with g1:
        headcount_growth = st.slider("Headcount growth (% YoY)", -5.0, 10.0, 2.0, 0.5) / 100
        graduate_growth = st.slider("Graduate growth (% YoY)", -5.0, 15.0, 3.0, 0.5) / 100
    with g2:
        research_growth = st.slider("Research output growth (% YoY)", -10.0, 20.0, 5.0, 0.5) / 100
        debt_growth = st.slider("Student debt growth (% YoY)", -10.0, 30.0, 8.0, 0.5) / 100
    with g3:
        capacity_growth = st.slider("Capacity growth (% YoY)", -2.0, 10.0, 1.5, 0.5) / 100
        staff_growth = st.slider("Academic staff growth (% YoY)", -2.0, 10.0, 1.5, 0.5) / 100

    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:14px;'>Policy parameters</h4>", unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        penalty_trigger = st.slider(
            "Penalty trigger: absolute plan deviation (%)",
            min_value=1.0, max_value=10.0, value=3.0, step=0.5,
            help="Absolute % deviation above which DHET removal applies. Default 3% per Ministerial Statement.",
        ) / 100
    with p2:
        funding_pool = st.number_input(
            "Internal funding pool (Rm)",
            min_value=0, max_value=2000, value=100, step=10,
            help="Internal reserves earmarked to absorb funding shocks.",
        )

    # Years to project
    years_ahead = st.slider("Years to project", 1, 5, 3)

    # Build year-by-year projection
    last_hc = float(latest_inst["ActualHeadcount"])
    last_grads = float(latest_inst["Graduates"])
    last_research = float(latest_inst["ResearchOutputUnits"])
    last_debt = float(latest_inst["StudentDebt_Rm"])
    last_capacity = float(latest_inst["CapacitySeats"])
    last_staff = float(latest_inst["AcademicStaffFTE"])
    last_plan = float(latest_inst["ApprovedPlanHeadcount"])
    last_tiu = float(latest_inst["TIU_proxy"])

    rows = []
    hc, grads, research, debt, capacity, staff, tiu, plan = (
        last_hc, last_grads, last_research, last_debt, last_capacity, last_staff, last_tiu, last_plan
    )
    for step in range(1, years_ahead + 1):
        year = latest_year + step
        hc = hc * (1 + headcount_growth)
        grads = grads * (1 + graduate_growth)
        research = research * (1 + research_growth)
        debt = debt * (1 + debt_growth)
        capacity = capacity * (1 + capacity_growth)
        staff = staff * (1 + staff_growth)
        # Assume plan grows at 2% (UP 2025) and TIU scales with headcount
        plan = plan * 1.02
        tiu = last_tiu * (hc / last_hc)

        deviation = (hc / plan) - 1
        # Apply user-defined penalty trigger
        trigger_breach = abs(deviation) > penalty_trigger
        if trigger_breach:
            # Removal rate escalates by year
            removal_rate = REMOVAL_RATE_2024 if step == 1 else (REMOVAL_RATE_2025 if step == 2 else REMOVAL_RATE_2026)
            excess_pct = abs(deviation) - penalty_trigger
            excess_units = excess_pct * plan * (tiu / hc) if hc > 0 else 0
            penalty = excess_units * removal_rate * RAND_PER_TIU_2026_27
        else:
            penalty = 0

        ssr = hc / staff if staff > 0 else np.nan
        cap_util = hc / capacity if capacity > 0 else np.nan

        rows.append({
            "Year": year,
            "Headcount": hc, "Graduates": grads, "Research output": research,
            "Student debt (Rm)": debt, "Capacity": capacity, "Staff FTE": staff,
            "Plan": plan, "Deviation %": deviation, "Trigger breach": trigger_breach,
            "Penalty (Rm)": penalty / 1_000_000,
            "Student-Staff Ratio": ssr, "Capacity utilisation": cap_util,
        })

    sc = pd.DataFrame(rows)
    total_penalty = sc["Penalty (Rm)"].sum()
    funding_gap = total_penalty - funding_pool

    # Key outcome metrics
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:14px;'>Outcome metrics</h4>", unsafe_allow_html=True)
    o1, o2, o3, o4 = st.columns(4)
    with o1:
        st.metric("Cumulative penalty", f"R{total_penalty:.1f}m", delta_color="inverse")
    with o2:
        st.metric("Internal funding pool", f"R{funding_pool:.0f}m")
    with o3:
        if funding_gap > 0:
            st.metric("Funding shortfall", f"R{funding_gap:.1f}m", delta_color="inverse")
        else:
            st.metric("Pool surplus", f"R{-funding_gap:.1f}m")
    with o4:
        end_hc = sc["Headcount"].iloc[-1]
        end_cap = sc["Capacity"].iloc[-1]
        st.metric(f"End-year cap utilisation", f"{end_hc/end_cap:.1%}",
                  delta_color="inverse" if end_hc/end_cap > 1.0 else "normal")

    # Commentary
    if funding_gap > 0:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_RED};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_RED};">⚠ Funding pool insufficient.</strong>
            Cumulative penalty of R{total_penalty:.1f}m exceeds the internal funding pool of R{funding_pool:.0f}m,
            leaving a R{funding_gap:.1f}m shortfall. Either increase the internal pool, reduce enrolment growth
            below the penalty trigger, or accept funding from operating reserves.
            </div>""",
            unsafe_allow_html=True,
        )
    elif total_penalty > 0:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_GOLD};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_GOLD};">Pool absorbs penalty.</strong>
            Cumulative R{total_penalty:.1f}m penalty is within the R{funding_pool:.0f}m pool,
            leaving R{-funding_gap:.1f}m headroom.
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid #2E7D32;border-radius:4px;margin:10px 0;">
            <strong style="color:#2E7D32;">No penalty triggered.</strong>
            Headcount growth of {headcount_growth:.1%} keeps deviation within the {penalty_trigger:.1%} trigger threshold.
            </div>""",
            unsafe_allow_html=True,
        )

    # Visualisation
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Scenario trajectory</h4>", unsafe_allow_html=True)
    fig = make_subplots(rows=2, cols=2, subplot_titles=(
        "Headcount and graduates", "Deviation from plan",
        "Capacity utilisation and SSR", "Cumulative penalty vs funding pool"
    ))
    fig.add_trace(go.Scatter(x=sc["Year"], y=sc["Headcount"], name="Headcount",
        line=dict(color=UP_BLUE, width=3), mode="lines+markers"), row=1, col=1)
    fig.add_trace(go.Scatter(x=sc["Year"], y=sc["Graduates"], name="Graduates",
        line=dict(color=UP_GOLD, width=3), mode="lines+markers"), row=1, col=1)

    fig.add_trace(go.Bar(x=sc["Year"], y=sc["Deviation %"] * 100,
        marker_color=[UP_RED if abs(v) > penalty_trigger else UP_GOLD for v in sc["Deviation %"]],
        name="Deviation %", showlegend=False), row=1, col=2)
    fig.add_hline(y=penalty_trigger * 100, line_dash="dot", line_color=UP_RED, row=1, col=2)
    fig.add_hline(y=-penalty_trigger * 100, line_dash="dot", line_color=UP_RED, row=1, col=2)

    fig.add_trace(go.Scatter(x=sc["Year"], y=sc["Capacity utilisation"] * 100,
        name="Cap utilisation %", line=dict(color=UP_BLUE, width=3), mode="lines+markers"), row=2, col=1)
    fig.add_trace(go.Scatter(x=sc["Year"], y=sc["Student-Staff Ratio"],
        name="SSR", line=dict(color=UP_RED, width=3, dash="dash"), mode="lines+markers", yaxis="y4"), row=2, col=1)

    cumulative_penalty = sc["Penalty (Rm)"].cumsum()
    fig.add_trace(go.Bar(x=sc["Year"], y=cumulative_penalty,
        marker_color=UP_RED, name="Cumulative penalty (Rm)", showlegend=False), row=2, col=2)
    fig.add_hline(y=funding_pool, line_dash="dash", line_color=UP_GOLD,
                  annotation_text=f"Pool R{funding_pool:.0f}m", row=2, col=2)

    fig.update_layout(height=600, plot_bgcolor="white",
                      legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="right", x=1))
    fig.update_xaxes(gridcolor=UP_LIGHT_GREY)
    fig.update_yaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig, use_container_width=True)

    # Detail table
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Detail</h4>", unsafe_allow_html=True)
    sc_display = sc.copy()
    sc_display["Year"] = sc_display["Year"].astype(int)
    sc_display["Trigger breach"] = sc_display["Trigger breach"].map({True: "Yes", False: "No"})
    st.dataframe(sc_display.style.format({
        "Headcount": "{:,.0f}", "Graduates": "{:,.0f}", "Research output": "{:,.0f}",
        "Student debt (Rm)": "R{:.0f}m", "Capacity": "{:,.0f}", "Staff FTE": "{:,.0f}",
        "Plan": "{:,.0f}", "Deviation %": "{:+.1%}", "Penalty (Rm)": "R{:.1f}m",
        "Student-Staff Ratio": "{:.1f}", "Capacity utilisation": "{:.1%}",
    }), use_container_width=True, hide_index=True)

# ===========================================================================
# TAB 2 - SHAPE AND SIZE SIMULATOR
# ===========================================================================
with tab2:
    st.markdown(f"<h3 style='color:{UP_BLUE};'>Shape and size shift simulator</h3>", unsafe_allow_html=True)
    st.caption(
        "Shift intake toward postgraduate and SET fields. Higher PG and SET shares both increase "
        "TIU weight per FTE and align with scarce-skills priorities."
    )

    latest_df = df[df["Year"] == latest_year]
    current_pg_share = latest_df[latest_df["Level"] == "PG"]["ActualHeadcount"].sum() / latest_df["ActualHeadcount"].sum()
    current_set_share = latest_df[latest_df["FundingGroup"] == "SET"]["ActualHeadcount"].sum() / latest_df["ActualHeadcount"].sum()
    current_headcount = float(latest_df["ActualHeadcount"].sum())

    st.markdown(f"<h4 style='color:{UP_BLUE};'>Current shape ({latest_year})</h4>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total headcount", f"{int(current_headcount):,}")
    with c2:
        st.metric("Current PG share", f"{current_pg_share:.1%}")
    with c3:
        st.metric("Current SET share", f"{current_set_share:.1%}")

    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:14px;'>Strategic mix</h4>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        new_pg_share = st.slider("New PG share (%)", 10.0, 50.0, max(current_pg_share * 100, 30.0), 1.0) / 100
    with c2:
        new_set_share = st.slider("New SET share (%)", 20.0, 70.0, max(current_set_share * 100, 55.0), 1.0) / 100

    result = shape_size_simulation(
        base_headcount=current_headcount, base_pg_share=current_pg_share,
        base_set_share=current_set_share, new_pg_share=new_pg_share, new_set_share=new_set_share,
        rand_per_tiu=RAND_PER_TIU_2026_27,
    )

    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:14px;'>Impact comparison</h4>", unsafe_allow_html=True)
    base, new = result["base"], result["new"]
    c1, c2, c3 = st.columns(3)
    with c1:
        delta_tiu_pct = (result["delta_tiu"] / base["tiu"]) * 100
        st.metric("Teaching Input Units", f"{int(new['tiu']):,}", f"{delta_tiu_pct:+.1f}%")
    with c2:
        delta_grad_pct = (result["delta_graduates"] / base["graduates"]) * 100
        st.metric("Graduates", f"{int(new['graduates']):,}", f"{delta_grad_pct:+.1f}%")
    with c3:
        st.metric("Implicit subsidy (Rm)", f"R{new['subsidy']/1_000_000:,.0f}m",
                  f"R{result['delta_subsidy']/1_000_000:+,.0f}m")

    cats = ["TIU (000s)", "Graduates (000s)", "Subsidy (Rm)"]
    base_vals = [base["tiu"]/1_000, base["graduates"]/1_000, base["subsidy"]/1_000_000]
    new_vals = [new["tiu"]/1_000, new["graduates"]/1_000, new["subsidy"]/1_000_000]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Current", x=cats, y=base_vals, marker_color=UP_BLUE,
        text=[f"{v:,.1f}" for v in base_vals], textposition="outside"))
    fig.add_trace(go.Bar(name="New mix", x=cats, y=new_vals, marker_color=UP_GOLD,
        text=[f"{v:,.1f}" for v in new_vals], textposition="outside"))
    fig.update_layout(height=400, plot_bgcolor="white", barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_yaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig, use_container_width=True)

    if result["delta_tiu"] > 0 and result["delta_graduates"] > 0:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid #2E7D32;border-radius:4px;margin:10px 0;">
            <strong style="color:#2E7D32;">Strategic improvement.</strong>
            Shifting to {new_pg_share:.0%} PG and {new_set_share:.0%} SET increases TIU by {delta_tiu_pct:+.1f}%,
            graduates by {delta_grad_pct:+.1f}%, and implicit subsidy by R{result['delta_subsidy']/1_000_000:+,.0f}m.
            </div>""",
            unsafe_allow_html=True,
        )

# ===========================================================================
# TAB 3 - FACULTY AND FUNDING GROUP VIEW
# ===========================================================================
with tab3:
    st.markdown(f"<h3 style='color:{UP_BLUE};'>Disaggregation by faculty and funding group</h3>", unsafe_allow_html=True)
    st.caption("Where does the scenario impact concentrate? Faculty and funding group analysis.")

    # Faculty breakdown
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:14px;'>Faculty profile ({latest_year})</h4>", unsafe_allow_html=True)

    fac_latest = fac[fac["Year"] == latest_year].copy()
    fac_latest = fac_latest.sort_values("ActualHeadcount", ascending=False)

    fig_f = make_subplots(rows=1, cols=2, subplot_titles=("Headcount and TIU by Faculty", "Subsidy proxies"))
    fig_f.add_trace(go.Bar(y=fac_latest["FacultyCode"], x=fac_latest["ActualHeadcount"],
        orientation="h", name="Headcount", marker_color=UP_BLUE), row=1, col=1)
    fig_f.add_trace(go.Bar(y=fac_latest["FacultyCode"], x=fac_latest["TIU_proxy"],
        orientation="h", name="TIU", marker_color=UP_GOLD), row=1, col=1)

    fig_f.add_trace(go.Bar(y=fac_latest["FacultyCode"], x=fac_latest["GraduateConversion"] * 100,
        orientation="h", name="Grad conv %", marker_color=UP_RED, showlegend=False), row=1, col=2)

    fig_f.update_layout(height=400, plot_bgcolor="white", barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1))
    fig_f.update_xaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig_f, use_container_width=True)

    # Funding group breakdown
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:14px;'>Funding group profile ({latest_year})</h4>", unsafe_allow_html=True)

    fg_latest = df[df["Year"] == latest_year].groupby("FundingGroup").agg(
        ActualHeadcount=("ActualHeadcount", "sum"),
        FTE=("FTE", "sum"),
        TIU_proxy=("TIU_proxy", "sum"),
        Graduates=("Graduates", "sum"),
        TuitionRevenue_Rm=("TuitionRevenue_Rm", "sum"),
    ).reset_index()
    fg_latest["TIU per FTE"] = fg_latest["TIU_proxy"] / fg_latest["FTE"]
    fg_latest["Subsidy_Rm"] = fg_latest["TIU_proxy"] * RAND_PER_TIU_2026_27 / 1_000_000

    fig_fg = make_subplots(rows=1, cols=2, subplot_titles=("Headcount and TIU by Funding Group", "TIU weight and implicit subsidy"))
    fig_fg.add_trace(go.Bar(x=fg_latest["FundingGroup"], y=fg_latest["ActualHeadcount"],
        name="Headcount", marker_color=UP_BLUE), row=1, col=1)
    fig_fg.add_trace(go.Bar(x=fg_latest["FundingGroup"], y=fg_latest["TIU_proxy"],
        name="TIU", marker_color=UP_GOLD), row=1, col=1)

    fig_fg.add_trace(go.Bar(x=fg_latest["FundingGroup"], y=fg_latest["TIU per FTE"],
        name="TIU per FTE", marker_color=UP_RED, showlegend=False), row=1, col=2)

    fig_fg.update_layout(height=400, plot_bgcolor="white", barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1))
    fig_fg.update_yaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig_fg, use_container_width=True)

    st.markdown("**Funding group detail**")
    st.dataframe(fg_latest.style.format({
        "ActualHeadcount": "{:,.0f}", "FTE": "{:,.0f}",
        "TIU_proxy": "{:,.0f}", "Graduates": "{:,.0f}",
        "TuitionRevenue_Rm": "R{:.0f}m", "TIU per FTE": "{:.3f}",
        "Subsidy_Rm": "R{:.0f}m",
    }), use_container_width=True, hide_index=True)

    st.caption(
        f"SET programmes carry TIU weights 1.5x to 5x higher than Business/General. "
        f"Each percentage point shifted toward SET increases the implicit subsidy yield "
        f"per FTE proportionally."
    )
