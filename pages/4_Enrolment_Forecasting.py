"""
Enrolment Forecasting page v3.

5-year forecasts anchored to the approved plan with 2% YoY growth cap.
UG/PG mix converging to 70/30 target. SET vs Business/General view.
Faculty disaggregation. No inflation from the 2023 outlier.
"""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.constants import (
    UP_2025_GROWTH_CAP, UP_2025_PG_TARGET_SHARE, UP_2025_UG_TARGET_SHARE,
    UP_2025_STUDENT_STAFF_RATIO_TARGET, UP_BLUE, UP_GOLD, UP_LIGHT_GREY, UP_RED,
)
from utils.data_loader import aggregate, load_enrolment_data
from utils.filters import apply_filters
from utils.forecasting import (
    constrained_institutional_forecast, funding_group_forecast,
    linear_forecast, ug_pg_mix_forecast,
)
from utils.theme import apply_theme, page_header

st.set_page_config(page_title="Enrolment Forecasting", layout="wide", page_icon="📈")
apply_theme()
page_header(
    "Enrolment Forecasting",
    "5-year projection anchored to approved plan with 2% YoY cap and 70/30 UG/PG mix target",
)

df_raw = load_enrolment_data()
df = apply_filters(df_raw)

if df.empty:
    st.warning("No data matches the current filters.")
    st.stop()

inst = aggregate(df, ["Year"])
latest_year = int(df["Year"].max())

# Methodology
with st.expander("Methodology and constraints", expanded=False):
    st.markdown(f"""
        **Forecast methodology**:
        - Plan-anchored baseline: forecast starts from the latest approved plan, not the latest actual.
          This prevents the 2023 enrolment outlier from inflating the projection.
        - Statistical models (linear regression, Holt-Winters) shown for reference only.
        - Constraints: {UP_2025_GROWTH_CAP:.0%} YoY growth cap at institutional level.

        **Mix targets**:
        - UG/PG mix converges from current to {UP_2025_UG_TARGET_SHARE:.0%}/{UP_2025_PG_TARGET_SHARE:.0%} over 5 years.
        - This shifts the institution toward research-led status (UP 2025).

        **Caveat**:
        - 8 years of annual data. Forecasts are indicative for direction and order of magnitude.
        - For precision, quarterly data and longer history are needed.
    """)

# Configuration
st.markdown(f"<h3 style='color:{UP_BLUE};'>Forecast configuration</h3>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    years_ahead = st.slider("Years to forecast", 1, 5, 5)
with c2:
    growth_cap = st.slider("YoY growth cap (%)", 0.0, 5.0, UP_2025_GROWTH_CAP * 100, 0.5) / 100
with c3:
    convergence_years = st.slider("Years to reach 70/30 mix", 1, 10, 5)

# ===========================================================================
# Institutional headcount forecast
# ===========================================================================
st.markdown(f"<h3 style='color:{UP_BLUE};margin-top:24px;'>Institutional headcount projection</h3>", unsafe_allow_html=True)

plan_series = inst.set_index("Year")["ApprovedPlanHeadcount"]
actual_series = inst.set_index("Year")["ActualHeadcount"]
fc = constrained_institutional_forecast(plan_series, actual_series, years_ahead, growth_cap, use_plan_baseline=True)

fig = go.Figure()
fig.add_trace(go.Scatter(x=actual_series.index, y=actual_series.values,
    name="Historical actual", line=dict(color=UP_RED, width=3), mode="lines+markers"))
fig.add_trace(go.Scatter(x=plan_series.index, y=plan_series.values,
    name="Historical plan", line=dict(color=UP_BLUE, width=3, dash="dash"), mode="lines+markers"))
fig.add_trace(go.Scatter(x=fc["Year"], y=fc["Plan-anchored capped"],
    name=f"Plan-anchored projection ({growth_cap:.0%} YoY)",
    line=dict(color=UP_GOLD, width=3), mode="lines+markers"))
fig.add_trace(go.Scatter(x=fc["Year"], y=fc["Statistical (unconstrained)"],
    name="Statistical (reference)", line=dict(color="#999", width=1, dash="dot"), mode="lines+markers"))
fig.add_trace(go.Scatter(x=list(fc["Year"]) + list(fc["Year"][::-1]),
                          y=list(fc["Upper 95%"]) + list(fc["Lower 95%"][::-1]),
                          fill="toself", fillcolor="rgba(150,150,150,0.10)",
                          line=dict(color="rgba(255,255,255,0)"), name="95% CI (reference)"))
fig.update_layout(height=420, plot_bgcolor="white", hovermode="x unified",
                  yaxis_title="Headcount", xaxis_title="Year",
                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
fig.update_xaxes(gridcolor=UP_LIGHT_GREY)
fig.update_yaxes(gridcolor=UP_LIGHT_GREY)
st.plotly_chart(fig, use_container_width=True)

# Narrative
last_plan = float(plan_series.iloc[-1])
last_actual = float(actual_series.iloc[-1])
projected_end = float(fc["Plan-anchored capped"].iloc[-1])

if last_actual > last_plan * 1.05:
    st.markdown(
        f"""<div style="background:white;padding:14px;border-left:4px solid {UP_GOLD};border-radius:4px;margin:10px 0;">
        <strong style="color:{UP_GOLD};">Plan vs actual gap.</strong>
        2025 actual ({int(last_actual):,}) exceeds plan ({int(last_plan):,}) by {(last_actual/last_plan-1)*100:.1f}%.
        The projection uses the plan baseline to set a sustainable trajectory.
        Reaching plan-anchored target of {int(projected_end):,} by {int(fc['Year'].iloc[-1])}
        requires rebalancing intake in the next admissions cycle.
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("**Forecast values**")
fc_display = fc.copy()
fc_display["Year"] = fc_display["Year"].astype(int)
st.dataframe(fc_display.style.format({
    "Plan-anchored capped": "{:,.0f}",
    "Statistical (unconstrained)": "{:,.0f}",
    "Lower 95%": "{:,.0f}",
    "Upper 95%": "{:,.0f}",
}), use_container_width=True, hide_index=True)

# ===========================================================================
# UG/PG mix forecast
# ===========================================================================
st.markdown(
    f"<hr style='border:none;height:2px;background:{UP_GOLD};margin:24px 0 16px 0;'/>",
    unsafe_allow_html=True,
)
st.markdown(f"<h3 style='color:{UP_BLUE};'>UG/PG mix forecast</h3>", unsafe_allow_html=True)
st.caption(
    f"UP is research-led. The strategic mix target is {UP_2025_UG_TARGET_SHARE:.0%} UG / "
    f"{UP_2025_PG_TARGET_SHARE:.0%} PG. The chart shows how UG and PG must move "
    f"if total enrolment is to grow at {growth_cap:.0%} and the mix is to converge to target."
)

ug_series = df[df["Level"] == "UG"].groupby("Year")["ActualHeadcount"].sum()
pg_series = df[df["Level"] == "PG"].groupby("Year")["ActualHeadcount"].sum()

if len(ug_series) < 2 or len(pg_series) < 2:
    st.warning("Not enough Level data under current filters to produce mix forecast.")
else:
    mix_fc = ug_pg_mix_forecast(
        ug_series, pg_series, years_ahead=years_ahead, growth_cap=growth_cap,
        target_ug_share=UP_2025_UG_TARGET_SHARE,
        target_pg_share=UP_2025_PG_TARGET_SHARE,
        convergence_years=convergence_years,
    )

    fig_mix = make_subplots(rows=1, cols=2,
                            subplot_titles=("UG vs PG headcount projection",
                                             "Share of total"))
    # Headcount
    fig_mix.add_trace(go.Scatter(x=ug_series.index, y=ug_series.values, name="UG actual",
        line=dict(color=UP_BLUE, width=3), mode="lines+markers"), row=1, col=1)
    fig_mix.add_trace(go.Scatter(x=pg_series.index, y=pg_series.values, name="PG actual",
        line=dict(color=UP_GOLD, width=3), mode="lines+markers"), row=1, col=1)
    fig_mix.add_trace(go.Scatter(x=mix_fc["Year"], y=mix_fc["UG"], name="UG projection",
        line=dict(color=UP_BLUE, width=2, dash="dash"), mode="lines+markers"), row=1, col=1)
    fig_mix.add_trace(go.Scatter(x=mix_fc["Year"], y=mix_fc["PG"], name="PG projection",
        line=dict(color=UP_GOLD, width=2, dash="dash"), mode="lines+markers"), row=1, col=1)

    # Share
    historical_shares = pd.DataFrame({"Year": ug_series.index})
    historical_shares["UG_share"] = ug_series.values / (ug_series.values + pg_series.values)
    historical_shares["PG_share"] = pg_series.values / (ug_series.values + pg_series.values)

    fig_mix.add_trace(go.Scatter(x=historical_shares["Year"], y=historical_shares["UG_share"] * 100,
        name="UG share %", line=dict(color=UP_BLUE, width=3), mode="lines+markers", showlegend=False), row=1, col=2)
    fig_mix.add_trace(go.Scatter(x=historical_shares["Year"], y=historical_shares["PG_share"] * 100,
        name="PG share %", line=dict(color=UP_GOLD, width=3), mode="lines+markers", showlegend=False), row=1, col=2)
    fig_mix.add_trace(go.Scatter(x=mix_fc["Year"], y=mix_fc["UG_share"] * 100,
        line=dict(color=UP_BLUE, width=2, dash="dash"), mode="lines+markers", showlegend=False), row=1, col=2)
    fig_mix.add_trace(go.Scatter(x=mix_fc["Year"], y=mix_fc["PG_share"] * 100,
        line=dict(color=UP_GOLD, width=2, dash="dash"), mode="lines+markers", showlegend=False), row=1, col=2)
    fig_mix.add_hline(y=UP_2025_UG_TARGET_SHARE * 100, line_dash="dot", line_color=UP_BLUE,
                       annotation_text=f"UG target {UP_2025_UG_TARGET_SHARE:.0%}", row=1, col=2)
    fig_mix.add_hline(y=UP_2025_PG_TARGET_SHARE * 100, line_dash="dot", line_color=UP_GOLD,
                       annotation_text=f"PG target {UP_2025_PG_TARGET_SHARE:.0%}", row=1, col=2)

    fig_mix.update_layout(height=420, plot_bgcolor="white", hovermode="x unified",
                          legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="right", x=1))
    fig_mix.update_xaxes(gridcolor=UP_LIGHT_GREY)
    fig_mix.update_yaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig_mix, use_container_width=True)

    # Current vs target
    last_ug_share = float(historical_shares["UG_share"].iloc[-1])
    last_pg_share = float(historical_shares["PG_share"].iloc[-1])
    pg_gap = UP_2025_PG_TARGET_SHARE - last_pg_share

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Current UG share", f"{last_ug_share:.1%}",
                  f"{(last_ug_share - UP_2025_UG_TARGET_SHARE)*100:+.1f}pp vs target")
    with c2:
        st.metric("Current PG share", f"{last_pg_share:.1%}",
                  f"{(last_pg_share - UP_2025_PG_TARGET_SHARE)*100:+.1f}pp vs target")
    with c3:
        st.metric("PG gap to close", f"{pg_gap*100:+.1f}pp")

    # Narrative
    if last_pg_share < UP_2025_PG_TARGET_SHARE - 0.05:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_RED};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_RED};">Mix gap.</strong>
            PG share of {last_pg_share:.1%} is {(UP_2025_PG_TARGET_SHARE-last_pg_share)*100:.1f}pp below the
            {UP_2025_PG_TARGET_SHARE:.0%} research-led target. Reaching the target requires either reducing UG intake
            or growing PG enrolment faster than UG. The projection shows the trajectory if UG enrolment stabilises
            and PG grows to absorb the institutional growth.
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("**Mix forecast values**")
    mix_display = mix_fc.copy()
    mix_display["Year"] = mix_display["Year"].astype(int)
    st.dataframe(mix_display.style.format({
        "Total": "{:,.0f}", "UG": "{:,.0f}", "PG": "{:,.0f}",
        "UG_share": "{:.1%}", "PG_share": "{:.1%}",
    }), use_container_width=True, hide_index=True)

# ===========================================================================
# Funding Group forecast (SET vs Business/General)
# ===========================================================================
st.markdown(
    f"<hr style='border:none;height:2px;background:{UP_GOLD};margin:24px 0 16px 0;'/>",
    unsafe_allow_html=True,
)
st.markdown(f"<h3 style='color:{UP_BLUE};'>Funding Group forecast (SET vs Business/General)</h3>", unsafe_allow_html=True)

set_series = df[df["FundingGroup"] == "SET"].groupby("Year")["ActualHeadcount"].sum()
bg_series = df[df["FundingGroup"] == "Business/General"].groupby("Year")["ActualHeadcount"].sum()

if len(set_series) < 2 or len(bg_series) < 2:
    st.info("Not enough FundingGroup data under current filters.")
else:
    fg_fc = funding_group_forecast(set_series, bg_series, years_ahead, growth_cap)

    fig_fg = go.Figure()
    fig_fg.add_trace(go.Scatter(x=set_series.index, y=set_series.values, name="SET actual",
        line=dict(color=UP_BLUE, width=3), mode="lines+markers"))
    fig_fg.add_trace(go.Scatter(x=bg_series.index, y=bg_series.values, name="Business/General actual",
        line=dict(color=UP_GOLD, width=3), mode="lines+markers"))
    fig_fg.add_trace(go.Scatter(x=fg_fc["Year"], y=fg_fc["SET"], name="SET projection",
        line=dict(color=UP_BLUE, width=2, dash="dash"), mode="lines+markers"))
    fig_fg.add_trace(go.Scatter(x=fg_fc["Year"], y=fg_fc["Business/General"], name="Business/General projection",
        line=dict(color=UP_GOLD, width=2, dash="dash"), mode="lines+markers"))
    fig_fg.update_layout(height=380, plot_bgcolor="white", hovermode="x unified",
                         yaxis_title="Headcount",
                         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig_fg.update_xaxes(gridcolor=UP_LIGHT_GREY)
    fig_fg.update_yaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig_fg, use_container_width=True)

    st.caption(
        f"SET programmes carry higher TIU weights (2.5x at undergraduate vs 1.5x for Business/General). "
        f"Sustaining SET growth aligns with scarce-skills priorities and increases subsidy yield per FTE."
    )

    st.markdown("**Funding Group forecast values**")
    fg_display = fg_fc.copy()
    fg_display["Year"] = fg_display["Year"].astype(int)
    st.dataframe(fg_display.style.format({col: "{:,.0f}" for col in fg_display.columns if col != "Year"}),
                 use_container_width=True, hide_index=True)
