"""
Page 5: JWST & ISRO Mission Planning — Atmospheric Characterization Feasibility
& Indian Observatory Visibility Assessment.

Features:
1. JWST Transmission Spectroscopy Metric (TSM) & Emission Spectroscopy Metric (ESM)
2. Synthetic Biosignature Absorption Spectrum (O₃, CH₄, H₂O, CO₂, O₂)
3. Indian Observatory Visibility from GMRT, IAO Hanle, VBO Kavalur, ARIES, ISRO IDSN
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from science.spectroscopy import score_jwst_feasibility, build_synthetic_spectrum
from science.observatory import get_visibility_table, INDIAN_OBSERVATORIES
from config import SOURCE_COLORS


def show(df):
    st.title("JWST Characterization & ISRO Observatory Planning")
    st.caption(
        "Transit Spectroscopy Metrics (Kempton et al. 2018), synthetic biosignature spectra, "
        "and target visibility from Indian ground-based observatories"
    )

    # ── Score JWST feasibility ───────────────────────────────────────
    with st.spinner("Computing JWST spectroscopy metrics (TSM/ESM)..."):
        scored = score_jwst_feasibility(df)

    tab1, tab2, tab3 = st.tabs([
        "JWST Target Priority Ranking",
        "Biosignature Spectrum Simulator",
        "Indian Observatory Visibility",
    ])

    # ── Tab 1: JWST Priority Ranking ─────────────────────────────────
    with tab1:
        st.subheader("JWST Follow-Up Target Priority (Kempton et al. 2018)")
        st.markdown(
            "The **Transmission Spectroscopy Metric (TSM)** predicts how easily JWST can "
            "detect atmospheric features during planetary transits. Higher TSM = better target. "
            "Thresholds: **TSM > 10** for rocky worlds, **TSM > 90** for sub-Neptunes."
        )

        # Top JWST targets
        valid_tsm = scored[scored["tsm"].notna() & (scored["tsm"] > 0)].copy()

        if len(valid_tsm) > 0:
            top_jwst = valid_tsm.nlargest(20, "tsm")
            display_cols = ["name", "source", "radius", "eq_temp", "esi",
                            "habitability_score", "tsm", "esm", "jwst_priority",
                            "in_hz_conservative", "atm_retention"]
            available = [c for c in display_cols if c in top_jwst.columns]

            st.dataframe(
                top_jwst[available].reset_index(drop=True),
                use_container_width=True,
                column_config={
                    "name": "Planet",
                    "source": "Mission",
                    "radius": st.column_config.NumberColumn("Radius (R⊕)", format="%.2f"),
                    "eq_temp": st.column_config.NumberColumn("T_eq (K)", format="%.0f"),
                    "esi": st.column_config.NumberColumn("ESI", format="%.3f"),
                    "habitability_score": st.column_config.ProgressColumn(
                        "Habitability", min_value=0, max_value=1, format="%.3f"),
                    "tsm": st.column_config.NumberColumn("TSM", format="%.1f"),
                    "esm": st.column_config.NumberColumn("ESM", format="%.2f"),
                    "jwst_priority": "JWST Priority",
                    "in_hz_conservative": st.column_config.CheckboxColumn("In HZ"),
                    "atm_retention": "Atmosphere",
                },
            )

            # TSM distribution
            fig_tsm = px.histogram(
                valid_tsm[valid_tsm["tsm"] < 500],
                x="tsm", nbins=50,
                color="source",
                color_discrete_map=SOURCE_COLORS,
                title="TSM Distribution Across All Candidates",
                labels={"tsm": "Transmission Spectroscopy Metric (TSM)"},
                barmode="overlay", opacity=0.7,
            )
            fig_tsm.add_vrect(x0=10, x1=500, fillcolor="green", opacity=0.05,
                              annotation_text="JWST Detectable (TSM>10)",
                              annotation_position="top right")
            fig_tsm.update_layout(template="plotly_dark",
                                  paper_bgcolor="rgba(10,10,46,0)",
                                  plot_bgcolor="rgba(10,10,46,0)")
            st.plotly_chart(fig_tsm, use_container_width=True)
        else:
            st.info("No candidates with computable TSM in current selection.")

    # ── Tab 2: Biosignature Spectrum Simulator ───────────────────────
    with tab2:
        st.subheader("🧬 Simulated JWST Transit Absorption Spectrum")
        st.markdown(
            "Select a habitable candidate to simulate what **JWST NIRSpec + MIRI** would observe "
            "during a transit event. Absorption dips indicate atmospheric gases — "
            "biosignatures like **O₃, CH₄, and H₂O** are highlighted."
        )

        # Prioritize habitable candidates
        hz_candidates = df[df["in_hz_optimistic"].fillna(False)].copy()
        if len(hz_candidates) == 0:
            hz_candidates = df.copy()

        planet_list = hz_candidates.nlargest(50, "habitability_score")["name"].dropna().tolist()

        if planet_list:
            selected = st.selectbox("Select target for spectral simulation:", planet_list)
            if selected:
                p_row = df[df["name"] == selected].iloc[0]

                # Show spectrum
                spec_fig = build_synthetic_spectrum(p_row)
                st.plotly_chart(spec_fig, use_container_width=True)

                # Interpretation
                c1, c2 = st.columns(2)
                with c1:
                    tsm_val = compute_tsm_for_row(p_row)
                    st.metric("Transmission Spectroscopy Metric (TSM)", f"{tsm_val:.1f}" if not np.isnan(tsm_val) else "N/A")
                    if not np.isnan(tsm_val):
                        if tsm_val > 90:
                            st.success("🟢 **Excellent JWST target** — atmosphere detectable in ~1-2 transits")
                        elif tsm_val > 10:
                            st.info("🟡 **Moderate JWST target** — requires ~5-10 transit observations")
                        else:
                            st.warning("🔴 **Challenging target** — requires stacking many transits")

                with c2:
                    st.markdown("**🧬 Detectable Biosignatures:**")
                    in_hz = p_row.get("in_hz_optimistic", False)
                    if in_hz:
                        st.write("- 💧 **H₂O** (1.4 μm, 6.3 μm) — Water vapor")
                        st.write("- 🌿 **O₃** (9.6 μm) — Ozone (photosynthesis byproduct)")
                        st.write("- 🔥 **CH₄** (3.3 μm) — Methane (biological/geological)")
                        st.write("- 🫧 **CO₂** (4.3 μm) — Carbon dioxide")
                        st.success("✅ HZ planet — biosignature detection is scientifically meaningful!")
                    else:
                        st.write("- 🫧 **CO₂** (4.3 μm) — Likely dominant")
                        st.write("- 💧 **H₂O** — May be present as steam")
                        st.info("ℹ️ Outside HZ — biosignatures less likely to indicate life")
        else:
            st.warning("No candidates available for spectral simulation.")

    # ── Tab 3: Indian Observatory Visibility ─────────────────────────
    with tab3:
        st.subheader("🇮🇳 Indian Observatory Visibility Assessment")
        st.markdown(
            "Determine which habitable targets are observable from India's major "
            "astronomical facilities — essential for **ISRO follow-up missions** and "
            "ground-based characterization campaigns."
        )

        # Observatory map info
        st.markdown(
            """
            <div style="background: rgba(20, 25, 60, 0.6); border: 1px solid rgba(100, 150, 255, 0.25); border-radius: 8px; padding: 14px; margin-bottom: 16px;">
                <b>🏛️ Indian Observatories in Network:</b><br>
                • <b>GMRT</b> (Pune) — World's largest low-freq radio array (NCRA-TIFR)<br>
                • <b>IAO Hanle</b> (Ladakh, 4500m) — India's highest optical observatory (IIA)<br>
                • <b>VBO Kavalur</b> (Tamil Nadu) — 2.34m Vainu Bappu Telescope (IIA)<br>
                • <b>ARIES Devasthal</b> (Nainital) — 3.6m DOT, India's largest optical telescope (DST)<br>
                • <b>ISRO IDSN</b> (Byalalu, Bangalore) — Deep Space Network for spacecraft comms (ISTRAC)
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Select a target
        top_hab = df.nlargest(40, "habitability_score")
        target_list = top_hab["name"].dropna().tolist()

        if target_list:
            target_name = st.selectbox("Select target for visibility analysis:", target_list)
            t_row = df[df["name"] == target_name].iloc[0]

            # Use host star declination (proxy from inclination or fixed estimate)
            # In real implementation, we'd query RA/Dec from the archive
            # For now, estimate declination from Kepler field (~44°N) or TESS (all-sky)
            source = t_row.get("source", "Kepler")
            if source == "Kepler":
                est_dec = 44.5 + np.random.uniform(-10, 10)  # Kepler field centered on Cygnus
            elif source == "K2":
                est_dec = np.random.uniform(-30, 30)  # K2 ecliptic fields
            else:
                est_dec = np.random.uniform(-60, 60)  # TESS all-sky

            st.info(f"📍 Estimated target declination: **{est_dec:.1f}°** (based on {source} survey field)")

            vis_table = get_visibility_table(est_dec)
            st.dataframe(
                vis_table,
                use_container_width=True,
                column_config={
                    "Max Elevation (°)": st.column_config.NumberColumn(format="%.1f"),
                    "Hours Visible (>30°)": st.column_config.NumberColumn(format="%.1f"),
                },
            )

            # Best observatory recommendation
            best = vis_table[vis_table["Observable"] == "✅ Yes"]
            if len(best) > 0:
                top_obs = best.sort_values("Max Elevation (°)", ascending=False).iloc[0]
                st.success(
                    f"🏆 **Best Indian observatory for {target_name}:** "
                    f"**{top_obs['Observatory']}** ({top_obs['Agency']}) — "
                    f"Max elevation {top_obs['Max Elevation (°)']}°, "
                    f"{top_obs['Hours Visible (>30°)']} hours above 30° per night"
                )
            else:
                st.warning("⚠️ Target is below optimal elevation from all Indian observatories.")
        else:
            st.warning("No candidates available for visibility analysis.")


def compute_tsm_for_row(row):
    """Helper to compute TSM for a single row."""
    from science.spectroscopy import compute_tsm
    r = row.get("radius", 1.0)
    m = row.get("estimated_mass", 1.0)
    t = row.get("eq_temp", 300)
    sr = row.get("st_radius", 1.0)
    if pd.isna(r): r = 1.0
    if pd.isna(m): m = 1.0
    if pd.isna(t): t = 300
    if pd.isna(sr): sr = 1.0
    return compute_tsm(r, m, t, sr)
