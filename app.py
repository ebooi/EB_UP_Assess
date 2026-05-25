"""
University of Pretoria - Institutional Analytics Dashboard v3.

Main entry. Applies global styling, presents landing page with description
of all six analytical domains.
"""
import streamlit as st

from utils.constants import APP_AUTHOR, APP_TITLE, APP_VERSION, UP_BLUE, UP_GOLD, UP_RED
from utils.data_loader import get_institutional_totals, load_enrolment_data
from utils.theme import apply_theme, page_header

st.set_page_config(
    page_title=APP_TITLE, page_icon="🎓",
    layout="wide", initial_sidebar_state="expanded",
)

apply_theme()
page_header(
    "UP Institutional Analytics",
    "Strategic Dashboard for the Vice-Chancellor and Executive",
)

# Landing description
st.markdown(
    f"""
    <div style="background:white;padding:20px;border-radius:6px;
                border-left:4px solid {UP_BLUE};margin-bottom:20px;">
        <h3 style="margin-top:0;color:{UP_BLUE};">About this dashboard</h3>
        <p style="margin-bottom:8px;line-height:1.6;">
            This dashboard supports strategic decision-making at the University of Pretoria
            by linking operational data to the funding instruments in the 2025 Ministerial
            Statement and to the targets in UP 2025.
        </p>
        <p style="margin-bottom:0;line-height:1.6;">
            <strong>Filters apply across all pages</strong> via the sidebar. Filter by
            faculty, programme cluster, level, funding group, and mode to focus the
            analysis on the cut that matters to your decision.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(f"<h3 style='color:{UP_BLUE};'>What is included</h3>", unsafe_allow_html=True)

col_left, col_right = st.columns(2)

with col_left:
    st.markdown(
        f"""
        <div style="background:white;padding:16px;border-radius:6px;
                    border-left:4px solid {UP_GOLD};margin-bottom:12px;">
            <h4 style="margin-top:0;color:{UP_BLUE};">1. Institutional Performance</h4>
            <p style="margin:0;font-size:14px;">
                Enrolment (Actual vs Plan with UG/PG breakdown, statistical analysis,
                executive narrative), Student Success (against DHET 80% sector benchmark),
                Efficiency, and Financial indicators. Full disaggregation by faculty,
                programme cluster, level, funding group, and mode.
            </p>
        </div>
        <div style="background:white;padding:16px;border-radius:6px;
                    border-left:4px solid {UP_GOLD};margin-bottom:12px;">
            <h4 style="margin-top:0;color:{UP_BLUE};">2. Subsidy and Strategic Risk</h4>
            <p style="margin:0;font-size:14px;">
                TIU, TOU, graduate conversion, output per FTE, and rand-value exposure
                under the DHET penalty regime.
            </p>
        </div>
        <div style="background:white;padding:16px;border-radius:6px;
                    border-left:4px solid {UP_GOLD};margin-bottom:12px;">
            <h4 style="margin-top:0;color:{UP_BLUE};">3. Data Governance</h4>
            <p style="margin:0;font-size:14px;">
                Eight governance principles with executive evidence, status indicators,
                owners, and key risks. Plus four data quality dimensions: completeness,
                accuracy, consistency, and reliability by faculty.
            </p>
        </div>
        <div style="background:white;padding:16px;border-radius:6px;
                    border-left:4px solid {UP_GOLD};margin-bottom:12px;">
            <h4 style="margin-top:0;color:{UP_BLUE};">4. Enrolment Forecasting</h4>
            <p style="margin:0;font-size:14px;">
                5-year forecasts anchored to the approved plan with 2% YoY growth cap,
                UG/PG mix converging to 70/30 target, and SET vs Business/General view.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_right:
    st.markdown(
        f"""
        <div style="background:white;padding:16px;border-radius:6px;
                    border-left:4px solid {UP_GOLD};margin-bottom:12px;">
            <h4 style="margin-top:0;color:{UP_BLUE};">5. What-If Scenarios</h4>
            <p style="margin:0;font-size:14px;">
                Expanded scenario inputs: headcount, graduate, research output,
                student debt, capacity, and staff growth. Penalty trigger threshold
                and internal funding pool sizing. Includes a shape-and-size simulator
                and disaggregation by faculty and funding group.
            </p>
        </div>
        <div style="background:white;padding:16px;border-radius:6px;
                    border-left:4px solid {UP_GOLD};margin-bottom:12px;">
            <h4 style="margin-top:0;color:{UP_BLUE};">6. Data Definition</h4>
            <p style="margin:0;font-size:14px;">
                Complete data dictionary for every field, with definitions, sources,
                refresh frequency, and calculation rules.
            </p>
        </div>
        <div style="background:white;padding:16px;border-radius:6px;
                    border-left:4px solid {UP_RED};margin-bottom:12px;">
            <h4 style="margin-top:0;color:{UP_BLUE};">Colour and status conventions</h4>
            <p style="margin:0;font-size:14px;">
                <strong style="color:{UP_BLUE};">UP Blue</strong> for headings.
                <strong style="color:{UP_RED};">Red</strong> for strategic risks and alerts.
                <strong style="color:{UP_GOLD};">Gold</strong> for highlights and dividers.
                Status: <strong style="color:#2E7D32;">Green</strong> compliant,
                <strong style="color:{UP_GOLD};">Amber</strong> watch,
                <strong style="color:{UP_RED};">Red</strong> breach.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Institutional snapshot
st.markdown(f"<h3 style='color:{UP_BLUE};margin-top:24px;'>Institutional snapshot</h3>", unsafe_allow_html=True)

df = load_enrolment_data()
inst = get_institutional_totals(df)
latest = inst.iloc[-1]
prior = inst.iloc[-2]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total enrolled (2025)",
              f"{int(latest['ActualHeadcount']):,}",
              f"{(latest['ActualHeadcount']/prior['ActualHeadcount']-1)*100:+.1f}% YoY")
with col2:
    st.metric("Total graduates (2025)",
              f"{int(latest['Graduates']):,}",
              f"{(latest['Graduates']/prior['Graduates']-1)*100:+.1f}% YoY")
with col3:
    st.metric("Research output units (2025)",
              f"{int(latest['ResearchOutputUnits']):,}",
              f"{(latest['ResearchOutputUnits']/prior['ResearchOutputUnits']-1)*100:+.1f}% YoY")
with col4:
    st.metric("Tuition revenue (2025, Rm)",
              f"R{latest['TuitionRevenue_Rm']:,.0f}m",
              f"{(latest['TuitionRevenue_Rm']/prior['TuitionRevenue_Rm']-1)*100:+.1f}% YoY")

st.markdown(
    f"<hr style='border:none;height:1px;background:{UP_GOLD};margin:24px 0 12px 0;'/>",
    unsafe_allow_html=True,
)
st.caption(f"{APP_AUTHOR}  |  Version {APP_VERSION}")
