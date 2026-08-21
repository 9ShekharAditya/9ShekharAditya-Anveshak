"""
Page 1: Dashboard — Overview of Exoplanet Candidates & Confirmation Pipeline.

Presents key astrophysicist & astrobiologist metrics, top habitable worlds, and telescope breakdowns.
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
    st.title("🏠 Exoplanet Confirmation & Habitability Dashboard")
    st.caption("Astrobiological scoring & orbital characterization of candidates from NASA Exoplanet Archive (Kepler, TESS, K2)")

    # ── Telescope Mission Summary Row ─────────────────────────────────
    st.markdown("### 🛰️ Observational Survey Catalogs")
    col_k, col_t, col_k2, col_conf = st.columns(4)

    with col_k:
        k_count = len(full_df[full_df["source"] == "Kepler"]) if full_df is not None else 0
        k_hz = int(full_df[full_df["source"] == "Kepler"]["in_hz_optimistic"].fillna(False).sum()) if full_df is not None else 0
        st.markdown(f"""
        <div style="background: rgba(52, 152, 219, 0.15); border: 1px solid #3498db; border-radius: 8px; padding: 12px;">
            <b style="color: #3498db; font-size: 15px;">🔭 Kepler Mission (KOI)</b><br>
            <span style="font-size: 20px; font-weight: bold; color: #ffffff;">{k_count:,}</span> candidates<br>
            <span style="color: #2ecc71; font-size: 12px;">🌿 {k_hz} in Habitable Zone</span>
        </div>
        """, unsafe_allow_html=True)

    with col_t:
        t_count = len(full_df[full_df["source"] == "TESS"]) if full_df is not None else 0
        t_hz = int(full_df[full_df["source"] == "TESS"]["in_hz_optimistic"].fillna(False).sum()) if full_df is not None else 0
        st.markdown(f"""
        <div style="background: rgba(230, 126, 34, 0.15); border: 1px solid #e67e22; border-radius: 8px; padding: 12px;">
            <b style="color: #e67e22; font-size: 15px;">🛰️ TESS Mission (TOI)</b><br>
            <span style="font-size: 20px; font-weight: bold; color: #ffffff;">{t_count:,}</span> candidates<br>
            <span style="color: #2ecc71; font-size: 12px;">🌿 {t_hz} in Habitable Zone</span>
        </div>
        """, unsafe_allow_html=True)

    with col_k2:
        k2_count = len(full_df[full_df["source"] == "K2"]) if full_df is not None else 0
        k2_hz = int(full_df[full_df["source"] == "K2"]["in_hz_optimistic"].fillna(False).sum()) if full_df is not None else 0
        st.markdown(f"""
        <div style="background: rgba(155, 89, 182, 0.15); border: 1px solid #9b59b6; border-radius: 8px; padding: 12px;">
            <b style="color: #9b59b6; font-size: 15px;">📡 K2 Mission</b><br>
            <span style="font-size: 20px; font-weight: bold; color: #ffffff;">{k2_count:,}</span> candidates<br>
            <span style="color: #2ecc71; font-size: 12px;">🌿 {k2_hz} in Habitable Zone</span>
        </div>
        """, unsafe_allow_html=True)

    with col_conf:
        conf_count = len(full_df[full_df["source"] == "Confirmed"]) if full_df is not None else 0
        conf_hz = int(full_df[full_df["source"] == "Confirmed"]["in_hz_optimistic"].fillna(False).sum()) if full_df is not None else 0
        st.markdown(f"""
        <div style="background: rgba(46, 204, 113, 0.15); border: 1px solid #2ecc71; border-radius: 8px; padding: 12px;">
            <b style="color: #2ecc71; font-size: 15px;">✅ Confirmed Catalog</b><br>
            <span style="font-size: 20px; font-weight: bold; color: #ffffff;">{conf_count:,}</span> confirmed<br>
            <span style="color: #2ecc71; font-size: 12px;">🌿 {conf_hz} in Habitable Zone</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Current Filter Telemetry Row ─────────────────────────────────
    total = len(df)
    in_hz = int(df["in_hz_optimistic"].fillna(False).sum())
    in_hz_con = int(df["in_hz_conservative"].fillna(False).sum())
    high_pot = int((df["habitability_tier"] == "High Potential").sum())
    earth_like = int((df["esi"] >= 0.80).sum())

    st.markdown("### 📊 Active Scope Metrics")
    metric_row([
        {"label": "Total Active Scope", "value": f"{total:,}"},
        {"label": "Conservative HZ (Liquid Water)", "value": f"{in_hz_con:,}"},
        {"label": "🟢 High Potential (Score ≥ 0.55)", "value": f"{high_pot:,}"},
        {"label": "Earth-like Analogues (ESI ≥ 0.80)", "value": f"{earth_like:,}"},
    ])

    st.markdown("---")

    # ── Top Habitable Candidates Table ───────────────────────────────
    st.subheader("🏆 Top Ranked Habitable Worlds (Kopparapu 2013 + Astrobiology Scoring)")
    st.caption("Ranked by composite score incorporating Habitable Zone position, rocky radius penalty, surface temperature suitability, and tidal locking.")

    top = df.nlargest(15, "habitability_score")
    display_cols = ["tier_emoji", "name", "source", "disposition", "radius", "eq_temp",
                    "insol", "esi", "habitability_score", "ai_confidence_pct",
                    "size_class", "tidal_lock", "atm_retention"]

    available = [c for c in display_cols if c in top.columns]
    st.dataframe(
        top[available].reset_index(drop=True),
        use_container_width=True,
        column_config={
            "tier_emoji": st.column_config.TextColumn("Tier", width="small"),
            "name": "Planet Identifier",
            "source": "Mission",
            "disposition": "Status",
            "radius": st.column_config.NumberColumn("Radius (R⊕)", format="%.2f"),
            "eq_temp": st.column_config.NumberColumn("T_eq (K)", format="%.0f"),
            "insol": st.column_config.NumberColumn("Insolation (S⊕)", format="%.3f"),
            "esi": st.column_config.NumberColumn("ESI", format="%.3f"),
            "habitability_score": st.column_config.ProgressColumn(
                "Habitability Score", min_value=0, max_value=1, format="%.3f"
            ),
            "ai_confidence_pct": st.column_config.ProgressColumn(
                "🤖 AI Confidence", min_value=0, max_value=100, format="%.0f%%"
            ),
            "size_class": "Regime",
            "tidal_lock": "Rotation",
            "atm_retention": "Atmosphere Retention",
        },
    )

    st.markdown("---")

    # ── Population Charts ────────────────────────────────────────────
    st.subheader("📈 Population Distribution & Insolation Plots")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(source_pie_chart(df), use_container_width=True)
    with c2:
        st.plotly_chart(tier_summary_chart(df), use_container_width=True)

    st.plotly_chart(radius_vs_insol_scatter(df), use_container_width=True)
