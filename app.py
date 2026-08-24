"""
app.py — Exoplanet Dashboard with Top Navigation Bar.
"""

import streamlit as st
import os

st.set_page_config(
    page_title="ANVESHAK — Exoplanet Dashboard",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from data.fetcher import get_unified_candidates
from science.habitability import score_habitability
from science.ai_model import predict_confirmation_confidence
from app_pages import dashboard, explorer, system_viewer, analytics, jwst_isro

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
    # Load data
    try:
        full_df = load_and_score_data()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    #  READ & MANAGE QUERY PARAMETERS 
    query_params = st.query_params
    active_page = query_params.get("page", "Dashboard")
    dataset_choice = query_params.get("dataset", "All Datasets")

    # If refresh requested, clear cache and clean URL
    if query_params.get("refresh") == "true":
        st.cache_data.clear()
        st.query_params.clear()
        st.query_params.update(page=active_page, dataset=dataset_choice)
        st.rerun()

    #  CUSTOM HTML TOP NAVBAR 
    navbar_html = f"""
    <div class="custom-navbar">
        <div class="nav-brand">ANVESHAK</div>
        <div class="nav-menu">
            <a class="nav-item {'active' if active_page == 'Dashboard' else ''}" href="?page=Dashboard&dataset={dataset_choice}" target="_self">Dashboard</a>
            <a class="nav-item {'active' if active_page == 'Exoplanets' else ''}" href="?page=Exoplanets&dataset={dataset_choice}" target="_self">Exoplanets</a>
            <a class="nav-item {'active' if active_page == '3D Viewer' else ''}" href="?page=3D+Viewer&dataset={dataset_choice}" target="_self">3D Viewer</a>
            <a class="nav-item {'active' if active_page == 'Analytics' else ''}" href="?page=Analytics&dataset={dataset_choice}" target="_self">Analytics</a>
            <a class="nav-item {'active' if active_page == 'JWST ISRO' else ''}" href="?page=JWST+ISRO&dataset={dataset_choice}" target="_self">JWST & ISRO</a>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <div class="nav-dropdown">
                <button class="dropbtn">Dataset: {dataset_choice} ▾</button>
                <div class="dropdown-content">
                    <a href="?page={active_page}&dataset=All+Datasets" target="_self">All Datasets</a>
                    <a href="?page={active_page}&dataset=Kepler" target="_self">Kepler (KOI)</a>
                    <a href="?page={active_page}&dataset=TESS" target="_self">TESS (TOI)</a>
                    <a href="?page={active_page}&dataset=K2" target="_self">K2 Candidates</a>
                    <a href="?page={active_page}&dataset=Confirmed" target="_self">Confirmed Planets</a>
                </div>
            </div>
            <a href="?page={active_page}&dataset={dataset_choice}&refresh=true" target="_self"
               style="text-decoration: none; color: #8a8070; border: 1px solid rgba(180, 155, 80, 0.2); 
                      padding: 6px 10px; border-radius: 6px; font-size: 13px; font-weight: 500; 
                      transition: all 0.2s; background: rgba(15,16,32,0.8);"
               onmouseover="this.style.color='#d4a843'; this.style.borderColor='rgba(212,168,67,0.5)';"
               onmouseout="this.style.color='#8a8070'; this.style.borderColor='rgba(180,155,80,0.2)';">
                🔄
            </a>
        </div>
    </div>
    """
    st.markdown(navbar_html, unsafe_allow_html=True)

    #  FILTER DATA BY SOURCE 
    source_map = {
        "Kepler": "Kepler",
        "TESS": "TESS",
        "K2": "K2",
        "Confirmed": "Confirmed",
    }
    if dataset_choice in source_map:
        df = full_df[full_df["source"] == source_map[dataset_choice]].copy()
    else:
        df = full_df.copy()

    #  RENDER PAGES 
    if active_page == "Dashboard":
        dashboard.show(df, full_df)
    elif active_page == "Exoplanets":
        explorer.show(df)
    elif active_page == "3D Viewer":
        system_viewer.show(df)
    elif active_page == "Analytics":
        analytics.show(df)
    elif active_page == "JWST ISRO" or active_page == "JWST & ISRO":
        jwst_isro.show(df)


if __name__ == "__main__":
    main()
