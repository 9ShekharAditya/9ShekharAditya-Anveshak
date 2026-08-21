"""
components/cards.py — Metric cards and detailed astrobiological assessment cards.
"""

import streamlit as st


def metric_row(metrics):
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.metric(
                label=m["label"],
                value=m["value"],
                delta=m.get("delta"),
            )


def planet_detail_card(row):
    tier = row.get("habitability_tier", "Unknown")
    emoji = row.get("tier_emoji", "")
    p_name = row.get("name", "Unknown Planet")

    st.markdown(f"### {emoji} **{p_name}** ({row.get('source', 'NASA Mission')})")

    # Habitable Zone Status Banner
    if row.get("in_hz_conservative"):
        st.success("✅ **Conservative Habitable Zone** (Kopparapu 2013: Liquid surface water possible under Earth-like greenhouse atmosphere)")
    elif row.get("in_hz_optimistic"):
        st.info("🔵 **Optimistic Habitable Zone** (Recent Venus / Early Mars boundary regime)")
    else:
        st.warning("⚠️ **Outside Habitable Zone** (Too scorched or frozen for surface liquid water)")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🌌 Orbital Mechanics**")
        st.write(f"- **Semi-Major Axis:** {row.get('semi_major_axis', 0):.4f} AU" if row.get('semi_major_axis') else "- **Semi-Major Axis:** N/A")
        st.write(f"- **Orbital Period:** {row.get('period', 0):.2f} days" if row.get('period') else "- **Period:** N/A")
        st.write(f"- **Eccentricity:** {row.get('eccentricity', 0):.3f}" if row.get('eccentricity') else "- **Eccentricity:** 0.000 (Circular)")
        st.write(f"- **Insolation Flux:** {row.get('insol', 1.0):.3f} S⊕")

    with col2:
        st.markdown("**🪐 Planetary Physical State**")
        st.write(f"- **Radius:** {row.get('radius', 1.0):.2f} R⊕ ({row.get('size_class', 'Unknown')})")
        st.write(f"- **Estimated Mass:** {row.get('estimated_mass', 1.0):.2f} M⊕")
        st.write(f"- **Escape Velocity (v_esc):** {row.get('escape_velocity_kms', 11.2):.1f} km/s")
        st.write(f"- **Equilibrium Temp (T_eq):** {row.get('eq_temp', 255):.0f} K")
        st.write(f"- **Estimated Surface Temp:** ~{row.get('eq_temp', 255) + 33:.0f} K (with 1 bar atmosphere)")

    with col3:
        st.markdown("**🔬 Astrobiology & Atmosphere**")
        st.write(f"- **Habitability Score:** **{row.get('habitability_score', 0):.3f}** / 1.000")
        st.write(f"- **Earth Similarity (ESI):** **{row.get('esi', 0):.3f}** / 1.000")
        st.write(f"- **Atmosphere Retention:** {row.get('atm_retention', 'Unknown')}")
        st.write(f"- **Tidal Locking:** {row.get('tidal_lock', 'Unknown')}")
        st.write(f"- **Stellar Flare Hazard:** {row.get('uv_flare_risk', 'Low')}")
        st.write(f"- **🤖 AI Confirmation:** {row.get('ai_confidence_pct', 50):.0f}% ({row.get('ai_validation_label', 'N/A')})")
