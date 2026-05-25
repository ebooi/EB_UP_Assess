"""
Data Governance page.
Eight principles with executive evidence, owners, status, key risks.
Four data quality dimensions: Completeness, Accuracy, Consistency, Reliability.
"""
from pathlib import Path
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.constants import (
    STATUS_GREEN, STATUS_AMBER, STATUS_RED,
    UP_BLUE, UP_GOLD, UP_LIGHT_GREY, UP_RED,
)
from utils.data_loader import load_enrolment_data
from utils.data_quality import (
    accuracy_by_faculty, all_dimensions_scorecard, completeness_by_faculty,
    consistency_by_faculty, get_all_issues, reliability_by_faculty,
)
from utils.filters import apply_filters
from utils.theme import apply_theme, page_header

st.set_page_config(page_title="Data Governance", layout="wide", page_icon="🔒")
apply_theme()
page_header(
    "Data Governance",
    "Eight principles with executive evidence, plus four data quality dimensions",
)

df_raw = load_enrolment_data()
df = apply_filters(df_raw)

if df.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# ---------------------------------------------------------------------------
# Eight principles - detailed
# ---------------------------------------------------------------------------
st.markdown(f"<h3 style='color:{UP_BLUE};'>Eight governance principles for executive oversight</h3>", unsafe_allow_html=True)
st.caption("Each principle includes: definition, executive evidence tracked, current status, owner, and key risks.")

PRINCIPLES = [
    {
        "title": "1. Accountability",
        "definition": "Named data owners are responsible for each data domain.",
        "evidence": "RACI matrix published; monthly stewardship review meetings.",
        "status": "Green", "owner": "Faculty officers, Research Office, Finance",
        "risk": "Owner turnover without handover. Mitigation: documented stewardship roles.",
    },
    {
        "title": "2. Transparency",
        "definition": "Definitions, sources, calculation rules, and refresh frequencies are documented.",
        "evidence": "Data Definition page populated for all fields; metadata visible on every chart.",
        "status": "Green", "owner": "Office of Institutional Analytics",
        "risk": "Definitions drift between systems. Mitigation: single source of truth in data dictionary.",
    },
    {
        "title": "3. Integrity & Quality",
        "definition": "Layered verification: HEMIS validation, internal reconciliation, analytical anomaly detection.",
        "evidence": "Live monitor below tracks completeness, accuracy, consistency, reliability per faculty.",
        "status": "Amber", "owner": "Office of Institutional Analytics; faculty officers",
        "risk": "R5m late/incorrect submission penalty; R20m disclaimer/adverse opinion penalty.",
    },
    {
        "title": "4. Security & Privacy",
        "definition": "Personal student data anonymised at analytical layer. POPIA compliance.",
        "evidence": "Access controls audit; quarterly POPIA self-assessment; encryption in transit and at rest.",
        "status": "Green", "owner": "ICT Security; Information Officer",
        "risk": "Insider access or breach. Mitigation: least-privilege access, log review.",
    },
    {
        "title": "5. Compliance",
        "definition": "HEMIS submission, annual reports, earmarked grant reports filed on time and accurate.",
        "evidence": "HEMIS due 31 July; annual report 30 July; UCDG/IEG progress 27 Feb; others 31 May.",
        "status": "Amber", "owner": "Registrar; Finance; Office of Institutional Analytics",
        "risk": "Penalties: R5m late HEMIS, R20m disclaimer opinion, R20m late annual report.",
    },
    {
        "title": "6. Accessibility",
        "definition": "Dashboard cascades from institutional view through faculty to programme level.",
        "evidence": "Filter panel on every page; role-based views planned for production.",
        "status": "Green", "owner": "Office of Institutional Analytics",
        "risk": "Insufficient data literacy at lower levels. Mitigation: stakeholder training programme.",
    },
    {
        "title": "7. Stakeholder Engagement",
        "definition": "Data literacy programme covering officers, registrars, deans, executive.",
        "evidence": "Quarterly governance forum; annual literacy assessment; data clinics.",
        "status": "Amber", "owner": "Office of Institutional Analytics; HR Learning & Development",
        "risk": "Slow adoption at faculty level. Mitigation: incentivised data champions network.",
    },
    {
        "title": "8. Continuous Improvement",
        "definition": "Quarterly review of issues, classifier performance, dashboard usage, remediation rate.",
        "evidence": "Quarterly governance dashboard; issue closure tracking; user feedback loop.",
        "status": "Amber", "owner": "Office of Institutional Analytics",
        "risk": "Inertia. Mitigation: explicit performance targets in stewardship contracts.",
    },
]

status_colour = {"Green": STATUS_GREEN, "Amber": STATUS_AMBER, "Red": STATUS_RED}

for i in range(0, len(PRINCIPLES), 2):
    col1, col2 = st.columns(2)
    for col, p in zip([col1, col2], PRINCIPLES[i:i+2]):
        with col:
            badge = status_colour[p["status"]]
            st.markdown(
                f"""<div style="background:white;padding:16px;border-left:4px solid {UP_GOLD};
                            border-radius:4px;margin-bottom:12px;min-height:280px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <h4 style="margin:0;color:{UP_BLUE};font-size:15px;">{p['title']}</h4>
                    <span style="background:{badge};color:white;padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;">{p['status']}</span>
                </div>
                <p style="margin:6px 0;font-size:13px;"><strong>Definition.</strong> {p['definition']}</p>
                <p style="margin:6px 0;font-size:13px;"><strong>Executive evidence.</strong> {p['evidence']}</p>
                <p style="margin:6px 0;font-size:13px;"><strong>Owner.</strong> {p['owner']}</p>
                <p style="margin:6px 0;font-size:13px;color:{UP_RED};"><strong>Key risk.</strong> {p['risk']}</p>
                </div>""",
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------------
# Four data quality dimensions
# ---------------------------------------------------------------------------
st.markdown(
    f"<hr style='border:none;height:2px;background:{UP_GOLD};margin:24px 0 16px 0;'/>",
    unsafe_allow_html=True,
)
st.markdown(f"<h3 style='color:{UP_BLUE};'>Data quality dimensions by faculty</h3>", unsafe_allow_html=True)
st.caption(
    "Four dimensions operationalised: Completeness (missing values), Accuracy (range validity), "
    "Consistency (cross-field rules), Reliability (year-on-year stability)."
)

scorecard = all_dimensions_scorecard(df)
latest_year = int(df["Year"].max())
latest_scorecard = scorecard[scorecard["Year"] == latest_year].copy()

# Aggregate KPIs
overall_completeness = latest_scorecard["Completeness"].mean()
overall_accuracy = latest_scorecard["Accuracy"].mean()
overall_consistency = latest_scorecard["Consistency"].mean()
overall_reliability = latest_scorecard["Reliability"].mean()
overall_avg = (overall_completeness + overall_accuracy + overall_consistency + overall_reliability) / 4

st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Aggregate scores ({latest_year})</h4>", unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Completeness", f"{overall_completeness:.1%}")
with col2:
    st.metric("Accuracy", f"{overall_accuracy:.1%}")
with col3:
    st.metric("Consistency", f"{overall_consistency:.1%}")
with col4:
    st.metric("Reliability", f"{overall_reliability:.1%}")
with col5:
    st.metric("Overall", f"{overall_avg:.1%}")

# Commentary
if overall_avg < 0.85:
    st.markdown(
        f"""<div style="background:white;padding:14px;border-left:4px solid {UP_RED};border-radius:4px;margin:10px 0;">
        <strong style="color:{UP_RED};">⚠ Audit risk.</strong>
        Aggregate data quality of {overall_avg:.1%} is below the 85% threshold typically required
        to survive an external HEMIS audit. The R5m late/incorrect submission penalty and the
        R20m disclaimer penalty become material.
        </div>""",
        unsafe_allow_html=True,
    )
elif overall_avg < 0.95:
    st.markdown(
        f"""<div style="background:white;padding:14px;border-left:4px solid {UP_GOLD};border-radius:4px;margin:10px 0;">
        <strong style="color:{UP_GOLD};">Watch.</strong>
        Aggregate data quality of {overall_avg:.1%} sits below the 95% executive comfort level.
        Investigate the dimension with the lowest score and the faculty driving that score.
        </div>""",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""<div style="background:white;padding:14px;border-left:4px solid #2E7D32;border-radius:4px;margin:10px 0;">
        <strong style="color:#2E7D32;">Healthy.</strong>
        Aggregate data quality of {overall_avg:.1%} exceeds 95%. Maintain current stewardship discipline.
        </div>""",
        unsafe_allow_html=True,
    )

# Dimension scorecard by faculty (heatmap)
st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Scorecard by faculty ({latest_year})</h4>", unsafe_allow_html=True)

dimensions_to_show = ["Completeness", "Accuracy", "Consistency", "Reliability", "Overall"]
heat_data = latest_scorecard[["Faculty"] + dimensions_to_show].set_index("Faculty")

fig_h = go.Figure(data=go.Heatmap(
    z=heat_data.values * 100,
    x=heat_data.columns, y=heat_data.index,
    colorscale=[[0, UP_RED], [0.7, UP_GOLD], [0.9, "#9bc99e"], [1, "#1A5F2B"]],
    zmin=50, zmax=100,
    text=[[f"{v:.0%}" if pd.notna(v) else "" for v in row] for row in heat_data.values],
    texttemplate="%{text}", textfont={"size": 12, "color": "white"},
    colorbar=dict(title="Score %"),
))
fig_h.update_layout(height=380, plot_bgcolor="white")
st.plotly_chart(fig_h, use_container_width=True)

# Trend per dimension
st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Dimension trends over time</h4>", unsafe_allow_html=True)
trend = scorecard.groupby("Year")[dimensions_to_show].mean().reset_index()
fig_t = go.Figure()
colours = {"Completeness": UP_BLUE, "Accuracy": UP_GOLD, "Consistency": UP_RED, "Reliability": "#6F42C1", "Overall": "#2E7D32"}
for dim in dimensions_to_show:
    fig_t.add_trace(go.Scatter(x=trend["Year"], y=trend[dim] * 100, name=dim,
                                 line=dict(color=colours[dim], width=2.5), mode="lines+markers"))
fig_t.update_layout(height=380, plot_bgcolor="white", yaxis_title="Score (%)",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
fig_t.update_xaxes(gridcolor=UP_LIGHT_GREY)
fig_t.update_yaxes(gridcolor=UP_LIGHT_GREY)
st.plotly_chart(fig_t, use_container_width=True)

# Issue drill-down
st.markdown(f"<h4 style='color:{UP_BLUE};margin-top:18px;'>Issue detail</h4>", unsafe_allow_html=True)
all_issues = get_all_issues(df)
if not all_issues.empty:
    issue_dim = st.selectbox(
        "Filter by dimension",
        options=["All"] + sorted(all_issues["Dimension"].unique().tolist())
    )
    show_issues = all_issues if issue_dim == "All" else all_issues[all_issues["Dimension"] == issue_dim]
    st.dataframe(show_issues, use_container_width=True, hide_index=True, height=300)

    csv = all_issues.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download all issues as CSV", data=csv,
                       file_name="data_quality_issues.csv", mime="text/csv")
else:
    st.success("No data quality issues detected under current filters.")
