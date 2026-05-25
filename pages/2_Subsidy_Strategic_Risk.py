"""
Subsidy and Strategic Risk page.
TIU, TOU, graduate conversion, output per FTE, and rand-value exposure.
"""
from pathlib import Path
import sys

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.calculations import calculate_subsidy_exposure, project_exposure_across_years
from utils.constants import (
    DHET_OVER_THRESHOLD, DHET_UNDER_THRESHOLD, RAND_PER_TIU_2026_27,
    REMOVAL_RATE_2024, REMOVAL_RATE_2025, REMOVAL_RATE_2026,
    UP_BLUE, UP_GOLD, UP_LIGHT_GREY, UP_RED,
)
from utils.data_loader import aggregate, load_enrolment_data
from utils.filters import apply_filters
from utils.theme import apply_theme, page_header

st.set_page_config(page_title="Subsidy and Strategic Risk", layout="wide", page_icon="⚠️")
apply_theme()
page_header(
    "Subsidy and Strategic Risk",
    "TIU, TOU, graduate conversion, and rand-value exposure under DHET penalty regime",
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

# KPIs
st.markdown(f"<h3 style='color:{UP_BLUE};'>Subsidy proxies ({latest_year})</h3>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Teaching Input Units (TIU)", f"{int(latest_inst['TIU_proxy']):,}")
with col2:
    st.metric("Teaching Output Units (TOU)", f"{int(latest_inst['TOU_proxy']):,}")
with col3:
    grad_conv = latest_inst["GraduateConversion"]
    st.metric("Graduate Conversion", f"{grad_conv:.1%}",
              help="Graduates / Actual headcount")
with col4:
    output_per_fte = latest_inst["OutputPerFTE"]
    st.metric("Output per FTE", f"{output_per_fte:.3f}")

if grad_conv < 0.18:
    st.markdown(
        f"""<div style="background:white;padding:14px;border-left:4px solid {UP_RED};border-radius:4px;margin:10px 0;">
        <strong style="color:{UP_RED};">⚠ Low graduate conversion.</strong>
        Only {grad_conv:.1%} of enrolled students graduated in {latest_year}. This signals subsidy compression.
        </div>""",
        unsafe_allow_html=True,
    )

# TIU vs TOU
st.markdown(f"<h3 style='color:{UP_BLUE};margin-top:24px;'>TIU vs TOU trajectory</h3>", unsafe_allow_html=True)
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=inst["Year"], y=inst["TIU_proxy"],
    name="Teaching Input Units", line=dict(color=UP_BLUE, width=3), mode="lines+markers"), secondary_y=False)
fig.add_trace(go.Scatter(x=inst["Year"], y=inst["TOU_proxy"],
    name="Teaching Output Units", line=dict(color=UP_GOLD, width=3), mode="lines+markers"), secondary_y=False)
fig.add_trace(go.Scatter(x=inst["Year"], y=inst["GraduateConversion"] * 100,
    name="Graduate conversion (%)", line=dict(color=UP_RED, width=3, dash="dash"), mode="lines+markers"), secondary_y=True)
fig.update_layout(height=400, plot_bgcolor="white", hovermode="x unified",
                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
fig.update_xaxes(gridcolor=UP_LIGHT_GREY)
fig.update_yaxes(title_text="Units", gridcolor=UP_LIGHT_GREY, secondary_y=False)
fig.update_yaxes(title_text="Conversion (%)", gridcolor=UP_LIGHT_GREY, secondary_y=True)
st.plotly_chart(fig, use_container_width=True)

# Subsidy exposure
st.markdown(f"<h3 style='color:{UP_BLUE};margin-top:24px;'>Rand-value subsidy exposure</h3>", unsafe_allow_html=True)

with st.expander("DHET penalty regime - context", expanded=False):
    st.markdown(f"""
        - Acceptable variance: DHET allows -2% under and +3% over.
        - Removal rates of excess units:
            - {REMOVAL_RATE_2024:.0%} for 2024 data (2026/27 financial year)
            - {REMOVAL_RATE_2025:.0%} for 2025 data (2027/28 financial year)
            - {REMOVAL_RATE_2026:.0%} for 2026 data (2028/29 financial year)
        - Implicit rand value per TIU: approximately R{RAND_PER_TIU_2026_27:,.0f}
    """)

actual_tiu = latest_inst["TIU_proxy"]
approved_tiu = actual_tiu * (latest_inst["ApprovedPlanHeadcount"] / latest_inst["ActualHeadcount"])
exposure_df = project_exposure_across_years(actual_tiu, approved_tiu)

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("**Exposure across removal-rate years**")
    st.dataframe(exposure_df.style.format({"Units removed": "{:,.0f}", "Rand exposure (Rm)": "R{:.1f}m"}),
                 use_container_width=True, hide_index=True)
    variance = (actual_tiu / approved_tiu) - 1
    if variance > DHET_OVER_THRESHOLD:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_RED};border-radius:4px;">
            <strong style="color:{UP_RED};">⚠ DHET breach.</strong>
            Over-enrolment of {variance:+.1%} exceeds the 3% ceiling.
            </div>""",
            unsafe_allow_html=True,
        )

with col2:
    fig_exp = go.Figure()
    fig_exp.add_trace(go.Bar(x=exposure_df["Financial year"], y=exposure_df["Rand exposure (Rm)"],
        marker_color=[UP_GOLD, "#D4843A", UP_RED],
        text=[f"R{v:.1f}m" for v in exposure_df["Rand exposure (Rm)"]], textposition="outside"))
    fig_exp.update_layout(height=350, plot_bgcolor="white",
                          yaxis_title="Rand exposure (Rm)",
                          title="Subsidy at risk under escalating removal rates",
                          showlegend=False)
    fig_exp.update_yaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig_exp, use_container_width=True)

# Financial risk
st.markdown(f"<h3 style='color:{UP_BLUE};margin-top:24px;'>Financial risk indicators</h3>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Tuition revenue", f"R{latest_inst['TuitionRevenue_Rm']:,.0f}m")
with col2:
    st.metric("Student debt", f"R{latest_inst['StudentDebt_Rm']:,.0f}m", delta_color="inverse")
with col3:
    st.metric("Debt-to-tuition", f"{latest_inst['DebtToTuition']:.1%}", delta_color="inverse")

# Faculty subsidy contribution
st.markdown(f"<h3 style='color:{UP_BLUE};margin-top:24px;'>Faculty subsidy contribution ({latest_year})</h3>", unsafe_allow_html=True)
fac_latest = fac[fac["Year"] == latest_year].copy().sort_values("TIU_proxy", ascending=True)
fig_f = go.Figure()
fig_f.add_trace(go.Bar(y=fac_latest["Faculty"], x=fac_latest["TIU_proxy"], orientation="h",
    marker_color=UP_BLUE,
    text=[f"{int(v):,}" for v in fac_latest["TIU_proxy"]], textposition="outside"))
fig_f.update_layout(height=400, plot_bgcolor="white",
                    xaxis_title="Teaching Input Units (TIU)", showlegend=False)
fig_f.update_xaxes(gridcolor=UP_LIGHT_GREY)
st.plotly_chart(fig_f, use_container_width=True)
