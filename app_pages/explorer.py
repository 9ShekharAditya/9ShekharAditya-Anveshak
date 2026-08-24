"""
Page 2: Explorer — Filterable table of candidates with deep scientific sorting & CSV export.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.filters import render_sidebar_filters
from components.cards import planet_detail_card


def show(df):
    st.title("🔎 Exoplanet Candidate & Confirmation Explorer")
    st.caption("Multi-variable scientific explorer: filter by mission survey, planetary radius, insolation, temperature, and habitability metrics")

    filtered = render_sidebar_filters(df)

    col1, col2 = st.columns([2, 1])
    with col1:
        sort_by = st.selectbox(
            "Sort by Metric:",
            ["habitability_score", "esi", "radius", "eq_temp", "period", "insol", "escape_velocity_kms"],
            format_func=lambda x: {
                "habitability_score": "Habitability Composite Score (↓)",
                "esi": "Earth Similarity Index (ESI) (↓)",
                "radius": "Planetary Radius (R⊕)",
                "eq_temp": "Equilibrium Temperature (K)",
                "period": "Orbital Period (days)",
                "insol": "Stellar Insolation Flux (S⊕)",
                "escape_velocity_kms": "Escape Velocity (km/s)",
            }.get(x, x),
        )
    with col2:
        ascending = st.checkbox("Ascending order", value=False)

    sorted_df = filtered.sort_values(sort_by, ascending=ascending, na_position="last")

    # Interactive Table 
    display_cols = ["tier_emoji", "name", "source", "disposition", "size_class", "radius",
                    "period", "eq_temp", "insol", "esi", "habitability_score",
                    "ai_confidence_pct", "atm_retention", "tidal_lock"]
    available = [c for c in display_cols if c in sorted_df.columns]

    st.dataframe(
        sorted_df[available].reset_index(drop=True),
        use_container_width=True,
        height=520,
        column_config={
            "tier_emoji": st.column_config.TextColumn("Tier", width="small"),
            "name": "Planet",
            "source": "Survey Mission",
            "disposition": "Status",
            "size_class": "Regime",
            "radius": st.column_config.NumberColumn("Radius (R⊕)", format="%.2f"),
            "period": st.column_config.NumberColumn("Period (d)", format="%.2f"),
            "eq_temp": st.column_config.NumberColumn("T_eq (K)", format="%.0f"),
            "insol": st.column_config.NumberColumn("Insolation", format="%.3f"),
            "esi": st.column_config.NumberColumn("ESI", format="%.3f"),
            "habitability_score": st.column_config.ProgressColumn(
                "Habitability Score", min_value=0, max_value=1, format="%.3f"
            ),
            "ai_confidence_pct": st.column_config.ProgressColumn(
                "🤖 AI Confidence", min_value=0, max_value=100, format="%.0f%%"
            ),
            "atm_retention": "Atmosphere Retention",
            "tidal_lock": "Rotation",
        },
    )

    #  Single Candidate Astrobiological Inspection 
    st.markdown("---")
    st.subheader("🔍 Individual Target In-Depth Telemetry")

    planet_names = sorted_df["name"].dropna().tolist()
    if planet_names:
        selected = st.selectbox("Select planet candidate to inspect:", planet_names)
        if selected:
            row = sorted_df[sorted_df["name"] == selected].iloc[0]
            planet_detail_card(row)

    #  Export 
    st.markdown("---")
    csv = filtered.to_csv(index=False)
    st.download_button(
        "📥 Export Filtered Dataset for Scientific Research (CSV)",
        data=csv,
        file_name="exoplanet_habitability_filtered_dataset.csv",
        mime="text/csv",
    )
