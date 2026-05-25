"""
Data Definition page.
Complete data dictionary for every field with sources and calculation rules.
"""
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.constants import UP_BLUE, UP_GOLD
from utils.data_loader import load_enrolment_data
from utils.filters import apply_filters
from utils.theme import apply_theme, page_header

st.set_page_config(page_title="Data Definition", layout="wide", page_icon="📖")
apply_theme()
page_header(
    "Data Definition",
    "Field definitions, sources, and calculation rules",
)

df_raw = load_enrolment_data()
df = apply_filters(df_raw)

# Source fields
st.markdown(f"<h3 style='color:{UP_BLUE};'>Source fields</h3>", unsafe_allow_html=True)
st.caption("Fields captured at programme cluster level in the source dataset.")

source_fields = pd.DataFrame([
    {"Field": "Year", "Type": "Integer", "Definition": "Academic year",
     "Source": "Student Information System", "Refresh": "Annual"},
    {"Field": "Faculty", "Type": "Text", "Definition": "Faculty name",
     "Source": "Student Information System", "Refresh": "Annual"},
    {"Field": "FacultyCode", "Type": "Text", "Definition": "Short faculty code",
     "Source": "Student Information System", "Refresh": "Annual"},
    {"Field": "ProgrammeCluster", "Type": "Text", "Definition": "Programme grouping within faculty",
     "Source": "Student Information System", "Refresh": "Annual"},
    {"Field": "CESM", "Type": "Integer", "Definition": "Classification of Educational Subject Matter",
     "Source": "HEMIS / DHET", "Refresh": "Annual"},
    {"Field": "Level", "Type": "Text", "Definition": "Qualification level (UG, PG)",
     "Source": "Student Information System", "Refresh": "Annual"},
    {"Field": "FundingGroup", "Type": "Text", "Definition": "DHET funding group (SET, Business/General)",
     "Source": "HEMIS / DHET", "Refresh": "Annual"},
    {"Field": "Mode", "Type": "Text", "Definition": "Tuition mode (Contact, Distance)",
     "Source": "Student Information System", "Refresh": "Annual"},
    {"Field": "ApprovedPlanHeadcount", "Type": "Integer", "Definition": "Ministerial-approved plan headcount",
     "Source": "DHET Ministerial Statement", "Refresh": "Annual"},
    {"Field": "ActualHeadcount", "Type": "Integer", "Definition": "Actual registered student headcount",
     "Source": "Student Information System", "Refresh": "Annual"},
    {"Field": "FTE", "Type": "Float", "Definition": "Full-time equivalent enrolment",
     "Source": "Student Information System", "Refresh": "Annual"},
    {"Field": "TeachingInputWeight", "Type": "Float", "Definition": "DHET funding weight from Table 3",
     "Source": "DHET Ministerial Statement", "Refresh": "When DHET updates"},
    {"Field": "TIU_proxy", "Type": "Float", "Definition": "Teaching Input Units (weighted FTE)",
     "Source": "Calculated: FTE x weight", "Refresh": "Annual"},
    {"Field": "Graduates", "Type": "Integer", "Definition": "Number of graduates in academic year",
     "Source": "Student Information System", "Refresh": "Annual"},
    {"Field": "TeachingOutputWeight", "Type": "Float", "Definition": "DHET teaching output weight",
     "Source": "DHET Ministerial Statement", "Refresh": "When DHET updates"},
    {"Field": "TOU_proxy", "Type": "Float", "Definition": "Teaching Output Units (weighted graduates)",
     "Source": "Calculated: Graduates x weight", "Refresh": "Annual"},
    {"Field": "ResearchOutputUnits", "Type": "Float", "Definition": "Weighted research outputs",
     "Source": "Research Information System", "Refresh": "Annual (15 October cut-off)"},
    {"Field": "AcademicStaffFTE", "Type": "Float", "Definition": "Academic staff full-time equivalent",
     "Source": "Human Resources", "Refresh": "Annual"},
    {"Field": "TuitionRevenue_Rm", "Type": "Float", "Definition": "Tuition revenue in million rands",
     "Source": "Finance system", "Refresh": "Annual"},
    {"Field": "StudentDebt_Rm", "Type": "Float", "Definition": "Outstanding student debt in million rands",
     "Source": "Finance system", "Refresh": "Annual"},
    {"Field": "CapacitySeats", "Type": "Integer", "Definition": "Approved capacity (seats)",
     "Source": "Space and facilities system", "Refresh": "Annual"},
    {"Field": "SuccessRate", "Type": "Float (0-1)", "Definition": "FTE-weighted course success rate",
     "Source": "Student Information System", "Refresh": "Annual"},
    {"Field": "DropoutRate", "Type": "Float (0-1)", "Definition": "Proportion who dropped out",
     "Source": "Student Information System", "Refresh": "Annual"},
])

st.dataframe(source_fields, use_container_width=True, hide_index=True, height=400)

# Derived fields
st.markdown(f"<h3 style='color:{UP_BLUE};margin-top:24px;'>Derived fields (calculated)</h3>", unsafe_allow_html=True)
st.caption("Fields computed at load time from the source data.")

derived = pd.DataFrame([
    {"Field": "VariancePct", "Calculation": "(ActualHeadcount / ApprovedPlanHeadcount) - 1",
     "Purpose": "Enrolment compliance against UP 2025 (2%) and DHET (-2%/+3%)"},
    {"Field": "RetentionRate", "Calculation": "1 - DropoutRate", "Purpose": "Student success indicator"},
    {"Field": "GraduationRate", "Calculation": "Graduates / ActualHeadcount",
     "Purpose": "Annual graduation rate per cohort"},
    {"Field": "StudentStaffRatio", "Calculation": "FTE / AcademicStaffFTE",
     "Purpose": "Efficiency indicator against UP 2025 24:1 target"},
    {"Field": "ResearchPerStaff", "Calculation": "ResearchOutputUnits / AcademicStaffFTE",
     "Purpose": "Research productivity against UP 2025 3.0 target"},
    {"Field": "CapacityUtilisation", "Calculation": "ActualHeadcount / CapacitySeats",
     "Purpose": "Infrastructure utilisation"},
    {"Field": "DebtToTuition", "Calculation": "StudentDebt_Rm / TuitionRevenue_Rm",
     "Purpose": "Financial sustainability"},
    {"Field": "GraduateConversion", "Calculation": "Graduates / ActualHeadcount",
     "Purpose": "Subsidy compression signal"},
    {"Field": "OutputPerFTE", "Calculation": "TOU_proxy / FTE", "Purpose": "Teaching output efficiency"},
])
st.dataframe(derived, use_container_width=True, hide_index=True)

# DHET context
st.markdown(f"<h3 style='color:{UP_BLUE};margin-top:24px;'>DHET funding context</h3>", unsafe_allow_html=True)
st.markdown(
    f"""<div style="background:white;padding:14px;border-left:4px solid {UP_GOLD};border-radius:4px;">
    <h4 style="margin-top:0;color:{UP_BLUE};">Block grant components</h4>
    <ul style="margin-bottom:0;">
        <li><strong>Teaching Input Sub-Block Grant</strong> - weighted FTEs (TIU)</li>
        <li><strong>Teaching Output Sub-Block Grant</strong> - weighted graduates (TOU)</li>
        <li><strong>Research Output Sub-Block Grant</strong> - doctoral graduates, publications, creative outputs</li>
        <li><strong>Institutional Factor Sub-Block Grant</strong> - disadvantaged students and institutional size</li>
    </ul>
    </div>""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""<div style="background:white;padding:14px;border-left:4px solid {UP_GOLD};border-radius:4px;margin-top:12px;">
    <h4 style="margin-top:0;color:{UP_BLUE};">Penalty regime</h4>
    <ul style="margin-bottom:0;">
        <li><strong>Enrolment variance</strong>: -2% to +3% acceptable; excess removed at 50% / 60% / 70% in successive years.</li>
        <li><strong>HEMIS submission</strong>: R5m for late or incorrect submission.</li>
        <li><strong>Audit opinion</strong>: R20m for disclaimer or adverse opinion.</li>
        <li><strong>Annual reports</strong>: R20m for late submission (R40m on repeat).</li>
    </ul>
    </div>""",
    unsafe_allow_html=True,
)

# Sample preview
st.markdown(f"<h3 style='color:{UP_BLUE};margin-top:24px;'>Sample data preview</h3>", unsafe_allow_html=True)
st.caption(f"First 10 rows under current filters ({len(df)} rows total).")
st.dataframe(df.head(10), use_container_width=True, hide_index=True)
