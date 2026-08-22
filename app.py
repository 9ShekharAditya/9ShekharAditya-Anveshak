"""
app.py — Exoplanet Confirmation & Habitability Dashboard.
"""

import streamlit as st
import os

st.set_page_config(
    page_title="Exoplanet Dashboard",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded",
)

from data.fetcher import get_unified_candidates
from science.habitability import score_habitability
from science.ai_model import predict_confirmation_confidence
from pages import dashboard, explorer, system_viewer, analytics, jwst_isro

# Inject custom CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner="🛰️ Fetching data from NASA Exoplanet Archive...")
def load_and_score_data():
    raw_df = get_unified_candidates(include_confirmed=True)
    scored_df = score_habitability(raw_df)
    final_df = predict_confirmation_confidence(scored_df)
    return final_df


def main():
    # ── Sidebar ──────────────────────────────────────────────────────
    st.sidebar.markdown("## 🪐 ANVESHAK")
    st.sidebar.caption("Cosmic Events")
    st.sidebar.markdown("---")

    # Load data
    try:
        full_df = load_and_score_data()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    # Telescope Adapter Source — shown in main content area on Dashboard
    st.sidebar.markdown("##### 🔭 Telescope Adapter Source")
    st.sidebar.markdown("Select Dataset:")
    mission_choice = st.sidebar.radio(
        "dataset",
        [
            "All Datasets Combined",
            "Kepler Candidates (Cumulative)",
            "TESS Candidates (TOI)",
            "K2 Candidates",
            "Confirmed Planets (Composite)",
        ],
        index=0,
        label_visibility="collapsed",
    )

    source_map = {
        "Kepler Candidates (Cumulative)": "Kepler",
        "TESS Candidates (TOI)": "TESS",
        "K2 Candidates": "K2",
        "Confirmed Planets (Composite)": "Confirmed",
    }

    if mission_choice in source_map:
        df = full_df[full_df["source"] == source_map[mission_choice]].copy()
    else:
        df = full_df.copy()

    st.sidebar.markdown("---")

    # Navigation
    nav = st.sidebar.radio(
        "navigation",
        [
            "Dashboard",
            "Exoplanet Analysis",
            "3D System Viewer",
            "Population Analytics",
            "JWST & ISRO Planning",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"**{len(df):,}** worlds loaded · "
        f"**{int(df['in_hz_optimistic'].fillna(False).sum()):,}** in HZ"
    )

    if st.sidebar.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # ── Page Routing ─────────────────────────────────────────────────
    if nav == "Dashboard":
        dashboard.show(df, full_df)
    elif nav == "Exoplanet Analysis":
        explorer.show(df)
    elif nav == "3D System Viewer":
        system_viewer.show(df)
    elif nav == "Population Analytics":
        analytics.show(df)
    elif nav == "JWST & ISRO Planning":
        jwst_isro.show(df)


if __name__ == "__main__":
    main()
