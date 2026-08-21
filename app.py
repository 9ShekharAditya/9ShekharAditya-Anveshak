"""
app.py — Main entrypoint for the Exoplanet Confirmation & Habitability Analysis Dashboard.
"""

import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Exoplanet Confirmation & Habitability Dashboard",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded",
)

from data.fetcher import get_unified_candidates
from science.habitability import score_habitability
from science.ai_model import predict_confirmation_confidence
from pages import dashboard, explorer, system_viewer, analytics

# Inject custom CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner="🛰️ Fetching telescope adapters & running AI confirmation engine...")
def load_and_score_data():
    raw_df = get_unified_candidates(include_confirmed=True)
    scored_df = score_habitability(raw_df)
    final_df = predict_confirmation_confidence(scored_df)
    return final_df


def main():
    # ── Sidebar Branding & Status ────────────────────────────────────
    st.sidebar.title("🪐 Exoplanet AI")
    st.sidebar.markdown(
        "**NASA Exoplanet Archive**  \n"
        "*Candidate Confirmation, Habitability & 3D Orbital Mechanics*"
    )
    st.sidebar.markdown("---")

    # Load Full Dataset
    try:
        full_df = load_and_score_data()
    except Exception as e:
        st.error(f"Error connecting to NASA Exoplanet Archive: {e}")
        return

    # ── Global Telescope / Mission Filter ────────────────────────────
    st.sidebar.subheader("🔭 Telescope Adapter Source")
    mission_choice = st.sidebar.radio(
        "Select Dataset:",
        [
            "🌌 All Datasets Combined",
            "🔭 Kepler Candidates (Cumulative)",
            "🛰️ TESS Candidates (TOI)",
            "📡 K2 Candidates",
            "✅ Confirmed Planets (Composite)",
        ],
        index=0,
    )

    if mission_choice == "🔭 Kepler Candidates (Cumulative)":
        df = full_df[full_df["source"] == "Kepler"].copy()
    elif mission_choice == "🛰️ TESS Candidates (TOI)":
        df = full_df[full_df["source"] == "TESS"].copy()
    elif mission_choice == "📡 K2 Candidates":
        df = full_df[full_df["source"] == "K2"].copy()
    elif mission_choice == "✅ Confirmed Planets (Composite)":
        df = full_df[full_df["source"] == "Confirmed"].copy()
    else:
        df = full_df.copy()

    st.sidebar.markdown("---")

    # ── Navigation ───────────────────────────────────────────────────
    st.sidebar.subheader("🧭 Page Navigation")
    nav = st.sidebar.radio(
        "Go to:",
        [
            "🏠 Dashboard",
            "🔎 Candidate Explorer",
            "🌌 3D System Viewer",
            "📈 Population Analytics",
        ],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.info(
        f"**Active Scope:**  \n"
        f"- Catalog: **{len(df):,} worlds** (out of {len(full_df):,} total)  \n"
        f"- In Habitable Zone: **{int(df['in_hz_optimistic'].fillna(False).sum()):,} worlds**  \n"
        f"- 🟢 High Potential: **{int((df['habitability_tier'] == 'High Potential').sum()):,} worlds**  \n"
        f"- 🤖 AI Confirmed Likelihood (>80%): **{int((df['ai_confidence_pct'] >= 80).sum()):,} worlds**"
    )

    if st.sidebar.button("🔄 Refresh Data Cache"):
        st.cache_data.clear()
        st.rerun()

    # ── Render Selected Page ─────────────────────────────────────────
    if nav == "🏠 Dashboard":
        dashboard.show(df, full_df)
    elif nav == "🔎 Candidate Explorer":
        explorer.show(df)
    elif nav == "🌌 3D System Viewer":
        system_viewer.show(df)
    elif nav == "📈 Population Analytics":
        analytics.show(df)


if __name__ == "__main__":
    main()
