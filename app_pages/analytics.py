"""
Page 4: Analytics — Statistical analysis, AI validation distribution, and population charts.

Deep-dive charts for understanding the candidate population:
- Radius distribution (with radius gap)
- Period vs. Radius (detection bias)
- HZ occupancy by mission
- ESI distribution
- Stellar type breakdown
- AI Confirmation Confidence distribution
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.plots import (
    radius_distribution, period_vs_radius_scatter,
    hz_occupancy_chart, esi_distribution, radius_vs_insol_scatter,
)
from config import SOURCE_COLORS


def show(df):
    st.title("📈 Population Analytics & AI Validation Engine")
    st.caption("Statistical analysis and AI-driven confirmation confidence for the exoplanet candidate population")

    # ── Overview stats ───────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        earth_sized = ((df["radius"] >= 0.8) & (df["radius"] <= 1.25)).sum()
        st.metric("Earth-sized (0.8–1.25 R⊕)", f"{earth_sized}")
    with col2:
        super_earths = ((df["radius"] > 1.25) & (df["radius"] <= 2.0)).sum()
        st.metric("Super-Earths (1.25–2.0 R⊕)", f"{super_earths}")
    with col3:
        sub_neptunes = ((df["radius"] > 2.0) & (df["radius"] <= 4.0)).sum()
        st.metric("Sub-Neptunes (2.0–4.0 R⊕)", f"{sub_neptunes}")
    with col4:
        gas_giants = (df["radius"] > 6.0).sum()
        st.metric("Gas Giants (>6.0 R⊕)", f"{gas_giants}")

    st.markdown("---")

    # ── Chart Tabs ───────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Radius Gap",
        "Period vs Radius",
        "Radius vs Insolation",
        "HZ Occupancy",
        "ESI Distribution",
        "Stellar Types",
        "AI Confirmation Confidence",
    ])

    with tab1:
        st.plotly_chart(radius_distribution(df), use_container_width=True)
        st.info(
            "The **Fulton radius gap** around 1.5–2.0 R⊕ is a real physical effect — "
            "planets in this range are rare because they either lose their "
            "H/He atmospheres via photoevaporation (becoming rocky super-Earths) "
            "or retain them (becoming gaseous sub-Neptunes)."
        )

    with tab2:
        st.plotly_chart(period_vs_radius_scatter(df), use_container_width=True)
        st.info(
            "The empty upper-right region shows a **geometric transit detection bias**: "
            "large planets on long orbits are harder to detect because they cross "
            "their star less frequently, reducing the number of observed transits."
        )

    with tab3:
        st.plotly_chart(radius_vs_insol_scatter(df), use_container_width=True)
        st.info(
            "Planets near Earth's insolation (1.0 S⊕) AND Earth's radius (1.0 R⊕) "
            "are the most promising for liquid surface water. The green band shows "
            "the conservative habitable zone flux range (Kopparapu 2013)."
        )

    with tab4:
        st.plotly_chart(hz_occupancy_chart(df), use_container_width=True)
        st.info(
            "Most candidates are **outside** the habitable zone — this is "
            "because close-in planets with short orbital periods are geometrically "
            "easiest to detect via the transit method."
        )

    with tab5:
        st.plotly_chart(esi_distribution(df), use_container_width=True)
        st.info(
            "**ESI ≥ 0.8** means the planet is physically similar to Earth "
            "in terms of radius, bulk density, escape velocity, and surface temperature. "
            "These are the strongest candidates for further spectroscopic follow-up."
        )

    with tab6:
        temp_valid = df[df["st_teff"].notna()].copy()
        if len(temp_valid) > 0:
            bins = [0, 3500, 5000, 6000, 7500, 15000]
            labels = ["M-dwarf (<3500K)", "K-star (3500–5000K)",
                      "G-star (5000–6000K)", "F-star (6000–7500K)",
                      "A-star (>7500K)"]
            temp_valid["star_type"] = pd.cut(
                temp_valid["st_teff"], bins=bins, labels=labels
            )

            type_counts = temp_valid.groupby(["star_type", "source"]).size().reset_index(name="count")

            fig = px.bar(
                type_counts,
                x="star_type",
                y="count",
                color="source",
                color_discrete_map=SOURCE_COLORS,
                title="Candidates by Host Star Spectral Type",
                labels={"star_type": "Spectral Type", "count": "Count"},
                barmode="group",
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(10,10,46,0)",
                plot_bgcolor="rgba(10,10,46,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

            st.info(
                "**M-dwarfs** are the most common stars in the galaxy and are "
                "prime targets for finding habitable planets because their "
                "habitable zones are close-in, making transits more frequent "
                "and increasing the geometric transit probability."
            )
        else:
            st.warning("No stellar temperature data available for this selection.")

    with tab7:
        # AI Confirmation Confidence Distribution
        if "ai_confidence_pct" in df.columns:
            candidates_only = df[df["disposition"] != "CONFIRMED"].copy()

            if len(candidates_only) > 0:
                fig_ai = px.histogram(
                    candidates_only,
                    x="ai_confidence_pct",
                    nbins=40,
                    color="source",
                    color_discrete_map=SOURCE_COLORS,
                    title="AI Confirmation Confidence Distribution (Candidates Only)",
                    labels={"ai_confidence_pct": "AI Confirmation Confidence (%)"},
                    barmode="overlay",
                    opacity=0.75,
                )

                # Add threshold regions
                fig_ai.add_vrect(x0=80, x1=100, fillcolor="green", opacity=0.08,
                                 annotation_text="High Likelihood (>80%)", annotation_position="top left")
                fig_ai.add_vrect(x0=0, x1=50, fillcolor="red", opacity=0.06,
                                 annotation_text="High False-Positive Risk (<50%)", annotation_position="top right")

                fig_ai.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(10,10,46,0)",
                    plot_bgcolor="rgba(10,10,46,0)",
                )
                st.plotly_chart(fig_ai, use_container_width=True)

                # Summary stats
                c1, c2, c3 = st.columns(3)
                with c1:
                    high_conf = (candidates_only["ai_confidence_pct"] >= 80).sum()
                    st.metric("High Confidence (>80%)", f"{high_conf:,}")
                with c2:
                    med_conf = ((candidates_only["ai_confidence_pct"] >= 50) & (candidates_only["ai_confidence_pct"] < 80)).sum()
                    st.metric("Moderate (50–80%)", f"{med_conf:,}")
                with c3:
                    low_conf = (candidates_only["ai_confidence_pct"] < 50).sum()
                    st.metric("False-Positive Risk (<50%)", f"{low_conf:,}")

                st.info(
                    "The **AI Confirmation Confidence Engine** uses multi-planet system validation "
                    "(Lissauer et al. 2012), radius feasibility, orbital period sanity checks, and "
                    "habitable zone consistency to estimate the probability that each candidate "
                    "is a true astrophysical planet rather than an instrumental false alarm or "
                    "eclipsing binary stellar blend."
                )
            else:
                st.info("No unconfirmed candidates in the current filter selection.")
        else:
            st.warning("AI confidence scores not available. Re-run the data pipeline.")

    # ── Summary statistics ───────────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Population Summary Statistics")

    stats_cols = ["radius", "period", "eq_temp", "insol", "esi", "habitability_score"]
    if "ai_confidence_pct" in df.columns:
        stats_cols.append("ai_confidence_pct")
    available_stats = [c for c in stats_cols if c in df.columns]

    stats = df[available_stats].describe().T
    stats.columns = ["Count", "Mean", "Std", "Min", "25%", "50%", "75%", "Max"]
    st.dataframe(stats, use_container_width=True)
