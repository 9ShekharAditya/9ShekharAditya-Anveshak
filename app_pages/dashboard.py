"""
Page 1: Dashboard — Mission Overview & Top Habitable Worlds.
"""

import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.cards import metric_row
from components.plots import (
    radius_vs_insol_scatter, source_pie_chart, tier_summary_chart
)


def show(df, full_df=None):
    st.title("Dashboard")
    st.caption(
        "Analysis and ranking of detected exoplanet candidates based on "
        "Earth Similarity Index (ESI) — [All Datasets Combined]"
    )

    #Mission Overview Metrics
    st.markdown("### Mission Overview")

    total = len(df)
    in_hz = int(df["in_hz_optimistic"].fillna(False).sum())
    high_pot = int((df["habitability_tier"] == "High Potential").sum())
    earth_like = int((df["esi"] >= 0.80).sum())

    metric_row([
        {"label": "Total Candidates", "value": f"{total:,}"},
        {"label": "In Habitable Zone", "value": f"{in_hz:,}"},
        {"label": "High Potential", "value": f"{high_pot:,}"},
        {"label": "Earth-like (ESI ≥ 0.8)", "value": f"{earth_like:,}"},
    ])

    # Show total analyzed count
    if full_df is not None and len(full_df) != len(df):
        st.caption(f"Total analysed: {len(full_df):,}")

    st.markdown("---")

    # Top Habitable Candidates 
    st.markdown("### Most Habitable Candidates (All Datasets Combined)")

    top = df.nlargest(15, "habitability_score")
    display_cols = ["tier_emoji", "name", "source", "radius", "eq_temp",
                    "insol", "esi", "habitability_score", "ai_confidence_pct",
                    "size_class", "tidal_lock", "in_hz_conservative"]

    available = [c for c in display_cols if c in top.columns]
    st.dataframe(
        top[available].reset_index(drop=True),
        use_container_width=True,
        column_config={
            "tier_emoji": st.column_config.TextColumn("Tier", width="small"),
            "name": "Planet",
            "source": "Mission",
            "radius": st.column_config.NumberColumn("Radius (R⊕)", format="%.2f"),
            "eq_temp": st.column_config.NumberColumn("Temp (K)", format="%.0f"),
            "insol": st.column_config.NumberColumn("Insol (S⊕)", format="%.3f"),
            "esi": st.column_config.NumberColumn("ESI", format="%.3f"),
            "habitability_score": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=1, format="%.3f"
            ),
            "ai_confidence_pct": st.column_config.ProgressColumn(
                "AI Conf.", min_value=0, max_value=100, format="%.0f%%"
            ),
            "size_class": "Size Class",
            "tidal_lock": "Tidal Lock",
            "in_hz_conservative": st.column_config.CheckboxColumn("In HZ"),
        },
    )

    st.markdown("---")

    # Charts 
    st.markdown("### 📈 Population Distribution")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(source_pie_chart(df), use_container_width=True)
    with c2:
        st.plotly_chart(tier_summary_chart(df), use_container_width=True)

    st.plotly_chart(radius_vs_insol_scatter(df), use_container_width=True)
