"""
Institutional Performance page.

Four tabs: Enrolment, Student Success, Efficiency, Financial.
Enrolment includes UG/PG visualisation, summary table with colour-coded
variances, detailed statistical analysis, and executive narrative.
Student Success benchmarks against DHET 80% sector rate with faculty
and level disaggregation.
"""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.calculations import dhet_compliance, up_2025_compliance
from utils.constants import (
    CHART_PALETTE, DHET_OVER_THRESHOLD, DHET_SECTOR_SUCCESS_RATE_2025,
    DHET_UNDER_THRESHOLD, STATUS_AMBER, STATUS_GREEN, STATUS_RED,
    UP_2025_STUDENT_STAFF_RATIO_TARGET, UP_2025_SUCCESS_RATE_TARGET,
    UP_2025_VARIANCE_THRESHOLD, UP_BLUE, UP_GOLD, UP_LIGHT_GREY, UP_RED,
)
from utils.data_loader import (
    aggregate, get_level_totals, load_enrolment_data,
)
from utils.filters import apply_filters
from utils.statistics import (
    correlation_analysis, distribution_stats, forecast_accuracy_metric,
    plan_deviation_history, trend_regression, yoy_growth_stats,
)
from utils.theme import apply_theme, page_header

st.set_page_config(page_title="Institutional Performance", layout="wide", page_icon="📊")
apply_theme()
page_header(
    "Institutional Performance",
    "Enrolment, student success, efficiency, and financial indicators",
)

df_raw = load_enrolment_data()
df = apply_filters(df_raw)

if df.empty:
    st.warning("No data matches the current filters. Adjust filters in the sidebar.")
    st.stop()

inst = aggregate(df, ["Year"])
fac = aggregate(df, ["Year", "Faculty", "FacultyCode"])
level = aggregate(df, ["Year", "Level"])
latest_year = int(df["Year"].max())

tab1, tab2, tab3, tab4 = st.tabs(
    ["Enrolment", "Student Success", "Efficiency", "Financial"]
)

# ===========================================================================
# TAB 1 - ENROLMENT
# ===========================================================================
with tab1:
    st.markdown(f"<h3 style='color:{UP_BLUE};'>Enrolment: Actual vs Plan</h3>", unsafe_allow_html=True)

    latest_inst = inst[inst["Year"] == latest_year].iloc[0]
    variance = latest_inst["VariancePct"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Approved plan", f"{int(latest_inst['ApprovedPlanHeadcount']):,}")
    with col2:
        st.metric("Actual enrolled", f"{int(latest_inst['ActualHeadcount']):,}")
    with col3:
        st.metric("Variance", f"{variance:+.1%}")
    with col4:
        up_status = up_2025_compliance(variance)
        dhet_status = dhet_compliance(variance)
        st.markdown(f"**UP 2025 (±2%):** {up_status}")
        st.markdown(f"**DHET (-2% / +3%):** {dhet_status}")

    # Executive narrative
    if up_status == "Red" or dhet_status == "Red":
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_RED};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_RED};">⚠ Strategic alert.</strong>
            Enrolment variance of {variance:+.1%} breaches the 2025 ±2% internal threshold
            {'and the DHET ±3% ceiling. ' if dhet_status == 'Red' else 'although it remains within the DHET ±3% ceiling. '}
            The Subsidy and Strategic Risk page quantifies the rand-value exposure under the
            2025 DHET penalty regime. Executive action is required to
            rebalance the next admissions cycle.
            </div>""",
            unsafe_allow_html=True,
        )
    elif up_status == "Amber":
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_GOLD};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_GOLD};">Watch.</strong>
            Variance of {variance:+.1%} is within 1pp of the UP 2025 ±2% threshold.
            Monitor faculty-level distribution to prevent breach.
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid #2E7D32;border-radius:4px;margin:10px 0;">
            <strong style="color:#2E7D32;">Compliant.</strong>
            Variance of {variance:+.1%} is within both the 2025 ±2% threshold and the DHET ±3% ceiling.
            </div>""",
            unsafe_allow_html=True,
        )

    # UG/PG visualisation
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:24px;'>UG vs PG enrolment</h4>", unsafe_allow_html=True)

    level_data = level.copy()
    fig_lvl = make_subplots(rows=1, cols=2, subplot_titles=("Headcount by Level", "Share by Level"))
    for i, lvl in enumerate(["UG", "PG"]):
        sub = level_data[level_data["Level"] == lvl]
        if not sub.empty:
            colour = UP_BLUE if lvl == "UG" else UP_GOLD
            fig_lvl.add_trace(
                go.Bar(x=sub["Year"], y=sub["ActualHeadcount"],
                       name=lvl, marker_color=colour),
                row=1, col=1,
            )

    # Share chart
    year_totals = level_data.groupby("Year")["ActualHeadcount"].sum().reset_index().rename(columns={"ActualHeadcount": "Total"})
    share_data = level_data.merge(year_totals, on="Year")
    share_data["Share"] = share_data["ActualHeadcount"] / share_data["Total"]
    for lvl in ["UG", "PG"]:
        sub = share_data[share_data["Level"] == lvl]
        if not sub.empty:
            colour = UP_BLUE if lvl == "UG" else UP_GOLD
            fig_lvl.add_trace(
                go.Bar(x=sub["Year"], y=sub["Share"] * 100,
                       name=f"{lvl} %", marker_color=colour, showlegend=False),
                row=1, col=2,
            )
    fig_lvl.update_layout(height=400, plot_bgcolor="white", barmode="stack",
                          legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="right", x=1))
    fig_lvl.update_xaxes(gridcolor=UP_LIGHT_GREY)
    fig_lvl.update_yaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig_lvl, use_container_width=True)

    # Year-Level summary table
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Year-Level summary with colour-coded variance</h4>", unsafe_allow_html=True)
    st.caption("Variance above ±2% from approved plan is highlighted.")

    summary = level.copy()
    summary = summary[["Year", "Level", "ApprovedPlanHeadcount", "ActualHeadcount",
                       "FTE", "TIU_proxy", "VariancePct"]].sort_values(["Year", "Level"])
    summary.columns = ["Year", "Level", "Approved Plan", "HC Actual", "HC FTE", "TIU Proxy", "Variance"]

    def colour_variance(v):
        if pd.isna(v):
            return ""
        if abs(v) <= UP_2025_VARIANCE_THRESHOLD:
            return f"background-color: rgba(46,125,50,0.15); color: #2E7D32; font-weight: 600;"
        elif abs(v) <= UP_2025_VARIANCE_THRESHOLD + 0.01:
            return f"background-color: rgba(195,155,71,0.20); color: #8B6914; font-weight: 600;"
        else:
            return f"background-color: rgba(200,16,46,0.15); color: {UP_RED}; font-weight: 600;"

    styled = summary.style.format({
        "Approved Plan": "{:,.0f}",
        "HC Actual": "{:,.0f}",
        "HC FTE": "{:,.1f}",
        "TIU Proxy": "{:,.1f}",
        "Variance": "{:+.1%}",
    }).map(colour_variance, subset=["Variance"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Trend chart with dual thresholds
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:24px;'>Enrolment trend with dual thresholds</h4>", unsafe_allow_html=True)
    fig = go.Figure()
    plan = inst["ApprovedPlanHeadcount"]
    fig.add_trace(go.Scatter(x=inst["Year"], y=plan * (1 + DHET_OVER_THRESHOLD),
        line=dict(color="rgba(200,16,46,0.15)", dash="dot"), name="DHET +3% ceiling"))
    fig.add_trace(go.Scatter(x=inst["Year"], y=plan * (1 + DHET_UNDER_THRESHOLD),
        line=dict(color="rgba(200,16,46,0.15)", dash="dot"), name="DHET -2% floor"))
    fig.add_trace(go.Scatter(x=inst["Year"], y=plan * (1 + UP_2025_VARIANCE_THRESHOLD),
        line=dict(color=UP_GOLD, dash="dash"), name="UP 2025 +2%"))
    fig.add_trace(go.Scatter(x=inst["Year"], y=plan * (1 - UP_2025_VARIANCE_THRESHOLD),
        line=dict(color=UP_GOLD, dash="dash"), name="2025 -2%"))
    fig.add_trace(go.Scatter(x=inst["Year"], y=plan, name="Approved plan",
        line=dict(color=UP_BLUE, width=3, dash="dash"), mode="lines+markers"))
    fig.add_trace(go.Scatter(x=inst["Year"], y=inst["ActualHeadcount"], name="Actual",
        line=dict(color=UP_RED, width=3), mode="lines+markers"))
    fig.update_layout(height=400, plot_bgcolor="white", yaxis_title="Headcount", xaxis_title="Year",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(gridcolor=UP_LIGHT_GREY)
    fig.update_yaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig, use_container_width=True)

    # Faculty variance
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:24px;'>Faculty variance ({latest_year})</h4>", unsafe_allow_html=True)
    fac_latest = fac[fac["Year"] == latest_year].copy()
    fac_latest["UP_Status"] = fac_latest["VariancePct"].apply(up_2025_compliance)
    colour_map = {"Green": STATUS_GREEN, "Amber": STATUS_AMBER, "Red": STATUS_RED, "Unknown": "#999"}
    colours = [colour_map[s] for s in fac_latest["UP_Status"]]

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=fac_latest["FacultyCode"], y=fac_latest["VariancePct"] * 100,
        marker_color=colours,
        text=[f"{v:+.1%}" for v in fac_latest["VariancePct"]], textposition="outside"))
    fig2.add_hline(y=UP_2025_VARIANCE_THRESHOLD * 100, line_dash="dash", line_color=UP_GOLD, annotation_text="UP +2%")
    fig2.add_hline(y=-UP_2025_VARIANCE_THRESHOLD * 100, line_dash="dash", line_color=UP_GOLD, annotation_text="UP -2%")
    fig2.add_hline(y=DHET_OVER_THRESHOLD * 100, line_dash="dot", line_color=UP_RED, annotation_text="DHET +3%")
    fig2.add_hline(y=DHET_UNDER_THRESHOLD * 100, line_dash="dot", line_color=UP_RED, annotation_text="DHET -2%")
    fig2.update_layout(height=400, plot_bgcolor="white", yaxis_title="Variance (%)", showlegend=False)
    fig2.update_yaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig2, use_container_width=True)

    # ----- STATISTICAL ANALYSIS -----
    st.markdown(
        f"<hr style='border:none;height:2px;background:{UP_GOLD};margin:24px 0 16px 0;'/>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<h3 style='color:{UP_BLUE};'>📈 Statistical analysis</h3>", unsafe_allow_html=True)

    actual_series = inst.set_index("Year")["ActualHeadcount"]
    plan_series = inst.set_index("Year")["ApprovedPlanHeadcount"]
    grad_series = inst.set_index("Year")["Graduates"]

    # Trend regression
    trend_actual = trend_regression(actual_series)
    trend_plan = trend_regression(plan_series)

    st.markdown(f"<h4 style='color:{UP_BLUE};'>Trend regression analysis</h4>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Actual trend slope",
                  f"{trend_actual['slope']:+,.0f}/yr",
                  f"R²={trend_actual['r_squared']:.2f}")
    with c2:
        st.metric("Significance (actual)",
                  "Yes" if trend_actual["significant"] else "No",
                  f"p={trend_actual['p_value']:.3f}")
    with c3:
        st.metric("Plan trend slope",
                  f"{trend_plan['slope']:+,.0f}/yr",
                  f"R²={trend_plan['r_squared']:.2f}")
    with c4:
        st.metric("Significance (plan)",
                  "Yes" if trend_plan["significant"] else "No",
                  f"p={trend_plan['p_value']:.3f}")

    # Interpret
    if trend_actual["significant"] and trend_actual["slope"] > trend_plan["slope"] * 1.2:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_RED};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_RED};">📊 Statistical insight.</strong>
            Actual enrolment is growing faster than the approved plan (slope {trend_actual['slope']:+,.0f}/yr
            vs plan {trend_plan['slope']:+,.0f}/yr, p={trend_actual['p_value']:.3f}).
            The trend is statistically significant at the 5% level. This systematic over-enrolment
            increases DHET penalty exposure year on year.
            </div>""",
            unsafe_allow_html=True,
        )
    elif not trend_actual["significant"]:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_GOLD};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_GOLD};">📊 Statistical note.</strong>
            The enrolment trend is not statistically significant at 5% (p={trend_actual['p_value']:.3f}).
            Volatility in the series limits the conclusions that can be drawn. The 2023 outlier in the
            dummy data weakens the trend signal.
            </div>""",
            unsafe_allow_html=True,
        )

    # YoY growth analysis
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Year-on-year growth analysis</h4>", unsafe_allow_html=True)
    yoy_actual = yoy_growth_stats(actual_series)
    yoy_plan = yoy_growth_stats(plan_series)
    yoy_grad = yoy_growth_stats(grad_series)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**Actual enrolment**")
        st.markdown(f"Mean: **{yoy_actual['mean_growth']:+.1%}**")
        st.markdown(f"Std dev: {yoy_actual['std_growth']:.1%}")
        st.markdown(f"95% CI: [{yoy_actual['ci_lower']:+.1%}, {yoy_actual['ci_upper']:+.1%}]")
    with c2:
        st.markdown(f"**Approved plan**")
        st.markdown(f"Mean: **{yoy_plan['mean_growth']:+.1%}**")
        st.markdown(f"Std dev: {yoy_plan['std_growth']:.1%}")
        st.markdown(f"95% CI: [{yoy_plan['ci_lower']:+.1%}, {yoy_plan['ci_upper']:+.1%}]")
    with c3:
        st.markdown(f"**Graduates**")
        st.markdown(f"Mean: **{yoy_grad['mean_growth']:+.1%}**")
        st.markdown(f"Std dev: {yoy_grad['std_growth']:.1%}")
        st.markdown(f"95% CI: [{yoy_grad['ci_lower']:+.1%}, {yoy_grad['ci_upper']:+.1%}]")

    # Faculty variance distribution
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Faculty variance distribution</h4>", unsafe_allow_html=True)
    fac_variances = fac["VariancePct"].dropna()
    dist = distribution_stats(fac_variances)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Mean variance", f"{dist['mean']:+.1%}")
    with c2:
        st.metric("Median variance", f"{dist['median']:+.1%}")
    with c3:
        st.metric("Std deviation", f"{dist['std']:.1%}")
    with c4:
        st.metric("Outliers (IQR rule)", f"{dist['outliers']}")

    st.caption(
        f"Across {len(fac_variances)} faculty-year observations, the variance from plan has a mean of "
        f"{dist['mean']:+.1%} and standard deviation of {dist['std']:.1%}. "
        f"IQR bounds: [{dist['lower_bound']:+.1%}, {dist['upper_bound']:+.1%}]. "
        f"{dist['outliers']} faculty-year combinations fall outside these bounds and require investigation."
    )

    # Throughput correlation
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Throughput correlation analysis</h4>", unsafe_allow_html=True)
    enrol_growth = actual_series.pct_change().dropna()
    grad_growth = grad_series.pct_change().dropna()
    corr = correlation_analysis(enrol_growth, grad_growth)

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Enrol/grad growth correlation", f"{corr['correlation']:.2f}")
    with c2:
        st.metric("Significance", "Yes" if corr["significant"] else "No",
                  f"p={corr['p_value']:.3f}")

    if corr["correlation"] < 0.5 and not pd.isna(corr["correlation"]):
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_RED};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_RED};">📊 Throughput gap signal.</strong>
            Correlation between enrolment growth and graduate growth is only {corr['correlation']:.2f}.
            Enrolments are growing faster than graduates are converting. This is the subsidy compression
            signal: teaching input units rise while teaching output units lag, creating a structural
            funding shortfall.
            </div>""",
            unsafe_allow_html=True,
        )

    # Plan deviation history (MAPE)
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Forecast accuracy analysis</h4>", unsafe_allow_html=True)
    acc = forecast_accuracy_metric(df)
    c1, c2 = st.columns(2)
    with c1:
        st.metric("MAPE (Plan vs Actual)", f"{acc['mape']:.1%}",
                  help="Mean absolute percentage error of actual against approved plan")
    with c2:
        st.metric("Maximum absolute deviation", f"{acc['max_abs_dev_pct']:.1%}")

    if acc["mape"] > 0.05:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_GOLD};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_GOLD};">📊 Planning accuracy concern.</strong>
            The mean absolute percentage error between approved plan and actual is {acc['mape']:.1%},
            with the worst year reaching {acc['max_abs_dev_pct']:.1%}.
            Enrolment planning accuracy needs to be strengthened to support reliable DHET submissions.
            </div>""",
            unsafe_allow_html=True,
        )


# ===========================================================================
# TAB 2 - STUDENT SUCCESS
# ===========================================================================
with tab2:
    st.markdown(f"<h3 style='color:{UP_BLUE};'>Student Success Indicators</h3>", unsafe_allow_html=True)
    st.markdown(
        f"""<div style="background:white;padding:12px;border-left:4px solid {UP_GOLD};border-radius:4px;margin-bottom:14px;">
        <strong style="color:{UP_BLUE};">2025 DHET Sector Student Success Rate: 80%</strong>.
        UP performance is benchmarked against this sector figure.
        </div>""",
        unsafe_allow_html=True,
    )

    latest_df = df[df["Year"] == latest_year]
    avg_success = latest_df["SuccessRate"].mean()
    avg_dropout = latest_df["DropoutRate"].mean()
    avg_retention = 1 - avg_dropout
    avg_graduation = latest_df["GraduationRate"].mean()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Success rate", f"{avg_success:.1%}",
                  f"{(avg_success - DHET_SECTOR_SUCCESS_RATE_2025)*100:+.1f}pp vs DHET sector")
    with col2:
        st.metric("Retention rate", f"{avg_retention:.1%}")
    with col3:
        st.metric("Dropout rate", f"{avg_dropout:.1%}", delta_color="inverse")
    with col4:
        st.metric("Graduation rate", f"{avg_graduation:.1%}")

    # Commentary against DHET 80%
    if avg_success < DHET_SECTOR_SUCCESS_RATE_2025 - 0.05:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_RED};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_RED};">⚠ Below DHET sector benchmark.</strong>
            Average success rate of {avg_success:.1%} is more than 5 percentage points below the
            DHET 2025 sector benchmark of 80%. This compromises the teaching output subsidy and
            indicates a structural throughput problem.
            </div>""",
            unsafe_allow_html=True,
        )
    elif avg_success < DHET_SECTOR_SUCCESS_RATE_2025:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_GOLD};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_GOLD};">Below benchmark.</strong>
            Success rate of {avg_success:.1%} is {(DHET_SECTOR_SUCCESS_RATE_2025-avg_success)*100:.1f}pp below the DHET 80% sector benchmark.
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid #2E7D32;border-radius:4px;margin:10px 0;">
            <strong style="color:#2E7D32;">Above benchmark.</strong>
            Success rate of {avg_success:.1%} exceeds the DHET 80% sector benchmark.
            </div>""",
            unsafe_allow_html=True,
        )

    # Faculty x Level disaggregation
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Success rate by faculty and level ({latest_year})</h4>", unsafe_allow_html=True)
    fac_level = df[df["Year"] == latest_year].groupby(["Faculty", "Level"]).agg(
        SuccessRate=("SuccessRate", "mean"),
    ).reset_index()
    pivot = fac_level.pivot(index="Faculty", columns="Level", values="SuccessRate")

    # Heatmap
    fig_h = go.Figure(data=go.Heatmap(
        z=pivot.values * 100,
        x=pivot.columns, y=pivot.index,
        colorscale=[[0, UP_RED], [0.5, UP_GOLD], [0.8, "#9bc99e"], [1, "#1A5F2B"]],
        zmin=50, zmax=95,
        text=[[f"{v:.1%}" if pd.notna(v) else "" for v in row] for row in pivot.values],
        texttemplate="%{text}", textfont={"size": 13, "color": "white"},
        colorbar=dict(title="Success rate %"),
    ))
    fig_h.add_vline(x=-0.5, line_dash="dot", line_color=UP_GOLD)
    fig_h.update_layout(height=400, plot_bgcolor="white",
                        title=f"DHET 80% benchmark applies across all cells")
    st.plotly_chart(fig_h, use_container_width=True)

    # Trend chart
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Success and dropout trend</h4>", unsafe_allow_html=True)
    trend_data = df.groupby("Year").agg(
        SuccessRate=("SuccessRate", "mean"),
        DropoutRate=("DropoutRate", "mean"),
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend_data["Year"], y=trend_data["SuccessRate"] * 100,
        name="Success rate", line=dict(color=UP_BLUE, width=3), mode="lines+markers"))
    fig.add_trace(go.Scatter(x=trend_data["Year"], y=(1 - trend_data["DropoutRate"]) * 100,
        name="Retention rate", line=dict(color=UP_GOLD, width=3), mode="lines+markers"))
    fig.add_trace(go.Scatter(x=trend_data["Year"], y=trend_data["DropoutRate"] * 100,
        name="Dropout rate", line=dict(color=UP_RED, width=3, dash="dash"), mode="lines+markers"))
    fig.add_hline(y=DHET_SECTOR_SUCCESS_RATE_2025 * 100, line_dash="dot", line_color=UP_GOLD,
                  annotation_text="DHET 2025 sector: 80%")
    fig.update_layout(height=400, plot_bgcolor="white", yaxis_title="Rate (%)",
                      hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(gridcolor=UP_LIGHT_GREY)
    fig.update_yaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig, use_container_width=True)

    # Faculty success rate ranked
    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Faculty success rate ranked ({latest_year})</h4>", unsafe_allow_html=True)
    fac_success = df[df["Year"] == latest_year].groupby("Faculty")["SuccessRate"].mean().reset_index().sort_values("SuccessRate").dropna()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        y=fac_success["Faculty"], x=fac_success["SuccessRate"] * 100, orientation="h",
        marker_color=[UP_RED if v < 0.7 else UP_GOLD if v < DHET_SECTOR_SUCCESS_RATE_2025 else UP_BLUE for v in fac_success["SuccessRate"]],
        text=[f"{v:.1%}" for v in fac_success["SuccessRate"]], textposition="outside",
    ))
    fig3.add_vline(x=DHET_SECTOR_SUCCESS_RATE_2025 * 100, line_dash="dash", line_color=UP_GOLD,
                   annotation_text="DHET 80%")
    fig3.update_layout(height=400, plot_bgcolor="white", xaxis_title="Success rate (%)", showlegend=False)
    fig3.update_xaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig3, use_container_width=True)


# ===========================================================================
# TAB 3 - EFFICIENCY
# ===========================================================================
with tab3:
    st.markdown(f"<h3 style='color:{UP_BLUE};'>Efficiency Indicators</h3>", unsafe_allow_html=True)

    latest_inst = inst[inst["Year"] == latest_year].iloc[0]
    student_staff = latest_inst["StudentStaffRatio"]
    research_per_staff = latest_inst["ResearchPerStaff"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total FTE", f"{int(latest_inst['FTE']):,}")
    with col2:
        st.metric("Academic Staff FTE", f"{int(latest_inst['AcademicStaffFTE']):,}")
    with col3:
        st.metric("Student-Staff Ratio", f"{student_staff:.1f}",
                  f"{student_staff - UP_2025_STUDENT_STAFF_RATIO_TARGET:+.1f} vs target")
    with col4:
        st.metric("Research per Staff", f"{research_per_staff:.2f}")

    if student_staff > UP_2025_STUDENT_STAFF_RATIO_TARGET + 5:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_RED};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_RED};">⚠ Capacity stress.</strong>
            Student-staff ratio of {student_staff:.1f} exceeds UP 2025 target of {UP_2025_STUDENT_STAFF_RATIO_TARGET} by more than 5.
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:24px;'>Efficiency trends</h4>", unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=inst["Year"], y=inst["StudentStaffRatio"],
        name="Student-Staff Ratio", line=dict(color=UP_BLUE, width=3), mode="lines+markers"))
    fig.add_hline(y=UP_2025_STUDENT_STAFF_RATIO_TARGET, line_dash="dash", line_color=UP_GOLD,
                  annotation_text=f"UP 2025 target: {UP_2025_STUDENT_STAFF_RATIO_TARGET}")
    fig.update_layout(height=350, plot_bgcolor="white", yaxis_title="Student-Staff Ratio", hovermode="x unified")
    fig.update_xaxes(gridcolor=UP_LIGHT_GREY)
    fig.update_yaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:24px;'>Research output per staff by faculty ({latest_year})</h4>", unsafe_allow_html=True)
    fac_research = fac[fac["Year"] == latest_year].copy().sort_values("ResearchPerStaff", ascending=True)
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(y=fac_research["Faculty"], x=fac_research["ResearchPerStaff"], orientation="h",
        marker_color=UP_BLUE,
        text=[f"{v:.2f}" for v in fac_research["ResearchPerStaff"]], textposition="outside"))
    fig4.update_layout(height=400, plot_bgcolor="white", xaxis_title="Research output per academic staff FTE", showlegend=False)
    fig4.update_xaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig4, use_container_width=True)


# ===========================================================================
# TAB 4 - FINANCIAL
# ===========================================================================
with tab4:
    st.markdown(f"<h3 style='color:{UP_BLUE};'>Financial Indicators</h3>", unsafe_allow_html=True)

    latest_inst = inst[inst["Year"] == latest_year].iloc[0]
    prior_inst = inst[inst["Year"] == latest_year - 1].iloc[0] if (latest_year - 1) in inst["Year"].values else latest_inst
    debt_to_tuition = latest_inst["DebtToTuition"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tuition revenue (Rm)", f"R{latest_inst['TuitionRevenue_Rm']:,.0f}m",
                  f"{(latest_inst['TuitionRevenue_Rm']/prior_inst['TuitionRevenue_Rm']-1)*100:+.1f}% YoY")
    with col2:
        st.metric("Student debt (Rm)", f"R{latest_inst['StudentDebt_Rm']:,.0f}m",
                  f"{(latest_inst['StudentDebt_Rm']/prior_inst['StudentDebt_Rm']-1)*100:+.1f}% YoY",
                  delta_color="inverse")
    with col3:
        st.metric("Debt-to-Tuition", f"{debt_to_tuition:.1%}",
                  f"{(debt_to_tuition - prior_inst['DebtToTuition'])*100:+.1f}pp",
                  delta_color="inverse")
    with col4:
        st.metric("Revenue per FTE (R'000)",
                  f"R{latest_inst['TuitionRevenue_Rm']*1000/latest_inst['FTE']:,.0f}")

    if debt_to_tuition > 0.20:
        st.markdown(
            f"""<div style="background:white;padding:14px;border-left:4px solid {UP_RED};border-radius:4px;margin:10px 0;">
            <strong style="color:{UP_RED};">⚠ Debt stress.</strong>
            Debt-to-tuition ratio of {debt_to_tuition:.1%} exceeds 20%.
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:24px;'>Revenue, debt, and ratio trajectory</h4>", unsafe_allow_html=True)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=inst["Year"], y=inst["TuitionRevenue_Rm"], name="Tuition revenue (Rm)",
                          marker_color=UP_BLUE), secondary_y=False)
    fig.add_trace(go.Bar(x=inst["Year"], y=inst["StudentDebt_Rm"], name="Student debt (Rm)",
                          marker_color=UP_RED), secondary_y=False)
    fig.add_trace(go.Scatter(x=inst["Year"], y=inst["DebtToTuition"] * 100,
        name="Debt-to-tuition (%)", line=dict(color=UP_GOLD, width=3), mode="lines+markers"), secondary_y=True)
    fig.update_layout(height=420, plot_bgcolor="white", barmode="group", hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(gridcolor=UP_LIGHT_GREY)
    fig.update_yaxes(title_text="Rm", gridcolor=UP_LIGHT_GREY, secondary_y=False)
    fig.update_yaxes(title_text="Ratio (%)", gridcolor=UP_LIGHT_GREY, secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:24px;'>Debt-to-tuition by faculty ({latest_year})</h4>", unsafe_allow_html=True)
    fac_debt = fac[fac["Year"] == latest_year].copy().sort_values("DebtToTuition")
    fig5 = go.Figure()
    fig5.add_trace(go.Bar(y=fac_debt["Faculty"], x=fac_debt["DebtToTuition"] * 100, orientation="h",
        marker_color=[UP_RED if v > 0.20 else UP_GOLD if v > 0.15 else UP_BLUE for v in fac_debt["DebtToTuition"]],
        text=[f"{v:.1%}" for v in fac_debt["DebtToTuition"]], textposition="outside"))
    fig5.update_layout(height=400, plot_bgcolor="white", xaxis_title="Debt-to-Tuition (%)", showlegend=False)
    fig5.update_xaxes(gridcolor=UP_LIGHT_GREY)
    st.plotly_chart(fig5, use_container_width=True)
