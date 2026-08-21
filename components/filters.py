"""
components/filters.py — Sidebar filter widgets for the Explorer page.
"""

import streamlit as st
import numpy as np


def render_sidebar_filters(df):
    """
    Render filter widgets in the sidebar and return the filtered DataFrame.

    Parameters:
        df: the scored candidates DataFrame

    Returns:
        filtered DataFrame
    """
    st.sidebar.header("🔎 Filters")

    filtered = df.copy()

    # ── Source mission ────────────────────────────────────────────────
    sources = sorted(df["source"].unique().tolist())
    selected_sources = st.sidebar.multiselect(
        "Mission Source",
        options=sources,
        default=sources,
    )
    filtered = filtered[filtered["source"].isin(selected_sources)]

    # ── Habitability tier ────────────────────────────────────────────
    tiers = ["High Potential", "Moderate Potential", "Low Potential", "Not Habitable"]
    available_tiers = [t for t in tiers if t in df["habitability_tier"].values]
    selected_tiers = st.sidebar.multiselect(
        "Habitability Tier",
        options=available_tiers,
        default=available_tiers,
    )
    filtered = filtered[filtered["habitability_tier"].isin(selected_tiers)]

    # ── Planet radius ────────────────────────────────────────────────
    radius_valid = df["radius"].dropna()
    if len(radius_valid) > 0:
        r_min = float(radius_valid.min())
        r_max = min(float(radius_valid.max()), 30.0)  # cap for slider
        radius_range = st.sidebar.slider(
            "Planet Radius (R⊕)",
            min_value=r_min,
            max_value=r_max,
            value=(r_min, r_max),
            step=0.1,
        )
        filtered = filtered[
            (filtered["radius"] >= radius_range[0]) &
            (filtered["radius"] <= radius_range[1]) |
            filtered["radius"].isna()
        ]

    # ── Orbital period ───────────────────────────────────────────────
    period_valid = df["period"].dropna()
    if len(period_valid) > 0:
        p_min = float(period_valid.min())
        p_max = min(float(period_valid.max()), 1000.0)
        period_range = st.sidebar.slider(
            "Orbital Period (days)",
            min_value=p_min,
            max_value=p_max,
            value=(p_min, p_max),
            step=1.0,
        )
        filtered = filtered[
            (filtered["period"] >= period_range[0]) &
            (filtered["period"] <= period_range[1]) |
            filtered["period"].isna()
        ]

    # ── Equilibrium temperature ──────────────────────────────────────
    temp_valid = df["eq_temp"].dropna()
    if len(temp_valid) > 0:
        t_min = float(temp_valid.min())
        t_max = min(float(temp_valid.max()), 3000.0)
        temp_range = st.sidebar.slider(
            "Eq. Temperature (K)",
            min_value=t_min,
            max_value=t_max,
            value=(t_min, t_max),
            step=10.0,
        )
        filtered = filtered[
            (filtered["eq_temp"] >= temp_range[0]) &
            (filtered["eq_temp"] <= temp_range[1]) |
            filtered["eq_temp"].isna()
        ]

    # ── Tidal lock status ────────────────────────────────────────────
    tidal_options = ["All", "Likely Synchronous (Locked)", "Possibly Locked", "Unlikely Locked"]
    tidal_choice = st.sidebar.selectbox("Tidal Lock Status", tidal_options)
    if tidal_choice != "All":
        filtered = filtered[filtered["tidal_lock"] == tidal_choice]

    # ── In habitable zone only ───────────────────────────────────────
    hz_only = st.sidebar.checkbox("Show only HZ candidates", value=False)
    if hz_only:
        filtered = filtered[filtered["in_hz_optimistic"].fillna(False)]

    st.sidebar.markdown(f"**Showing {len(filtered)} / {len(df)} candidates**")

    return filtered
