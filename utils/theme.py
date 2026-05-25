"""
Theme helper.

Applies the UP brand styling and a consistent header (with logo) on every page.
"""
from pathlib import Path

import streamlit as st

from utils.constants import (
    UP_BLUE,
    UP_BLUE_LIGHT,
    UP_GOLD,
    UP_LIGHT_GREY,
    UP_RED,
)

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "up_logo.png"


def apply_theme():
    """Inject CSS for UP brand styling."""
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-color: {UP_LIGHT_GREY};
            }}
            h1, h2, h3 {{
                color: {UP_BLUE};
                font-family: 'Helvetica Neue', Arial, sans-serif;
            }}
            .stMetric {{
                background-color: white;
                padding: 16px;
                border-radius: 6px;
                border-left: 4px solid {UP_BLUE};
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            }}
            .up-header {{
                background: linear-gradient(90deg, {UP_BLUE} 0%, {UP_BLUE_LIGHT} 100%);
                color: white;
                padding: 18px 24px;
                border-radius: 6px;
                margin-bottom: 20px;
                border-bottom: 4px solid {UP_GOLD};
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            .up-header h1 {{
                color: white !important;
                margin: 0;
                font-size: 26px;
            }}
            .up-header p {{
                color: #E8E8E8;
                margin: 4px 0 0 0;
                font-size: 14px;
            }}
            .risk-card {{
                background-color: white;
                padding: 14px;
                border-left: 4px solid {UP_RED};
                border-radius: 4px;
                margin-bottom: 10px;
            }}
            .info-card {{
                background-color: white;
                padding: 14px;
                border-left: 4px solid {UP_GOLD};
                border-radius: 4px;
                margin-bottom: 10px;
            }}
            .good-card {{
                background-color: white;
                padding: 14px;
                border-left: 4px solid #2E7D32;
                border-radius: 4px;
                margin-bottom: 10px;
            }}
            section[data-testid="stSidebar"] {{
                background-color: {UP_BLUE};
            }}
            section[data-testid="stSidebar"] * {{
                color: white !important;
            }}
            section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {{
                color: white !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = ""):
    """Render the standard page header with logo and title."""
    col1, col2 = st.columns([1, 3])
    with col1:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=240)
    with col2:
        st.markdown(
            f"""
            <div style="padding-top: 12px;">
                <h1 style="color: {UP_BLUE}; margin: 0; font-size: 28px;">{title}</h1>
                <p style="color: {UP_BLUE_LIGHT}; margin: 4px 0 0 0; font-size: 14px;">{subtitle}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        f"<hr style='border: none; height: 3px; background: {UP_GOLD}; margin: 8px 0 20px 0;'/>",
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    """Return an inline-styled HTML status badge."""
    colours = {
        "Green": "#2E7D32",
        "Amber": UP_GOLD,
        "Red": UP_RED,
        "Unknown": "#6c757d",
    }
    colour = colours.get(status, "#6c757d")
    return (
        f"<span style='background:{colour};color:white;padding:4px 10px;"
        f"border-radius:4px;font-size:12px;font-weight:600;'>{status}</span>"
    )
