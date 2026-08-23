"""
science/spectroscopy.py — JWST Transit Spectroscopy Feasibility & Biosignature Simulator.

Implements:
1. Transmission Spectroscopy Metric (TSM) — Kempton et al. 2018
2. Emission Spectroscopy Metric (ESM) — Kempton et al. 2018
3. Synthetic atmospheric absorption spectrum with biosignature gas markers
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Scale factors from Kempton et al. 2018 Table 1
TSM_SCALE = {
    "terran": 0.190,       # R < 1.5
    "super_earth": 1.26,   # 1.5 <= R < 2.75
    "sub_neptune": 1.28,   # 2.75 <= R < 4.0
    "giant": 1.15,         # R >= 4.0
}

# Biosignature absorption wavelengths (microns) and labels
BIOSIGNATURES = [
    {"name": "H₂O", "wavelength": 1.4, "color": "#3498db", "width": 0.15},
    {"name": "CO₂", "wavelength": 4.3, "color": "#e74c3c", "width": 0.3},
    {"name": "O₃ (Ozone)", "wavelength": 9.6, "color": "#2ecc71", "width": 0.8},
    {"name": "CH₄ (Methane)", "wavelength": 3.3, "color": "#f39c12", "width": 0.2},
    {"name": "H₂O", "wavelength": 6.3, "color": "#3498db", "width": 0.4},
    {"name": "O₂", "wavelength": 0.76, "color": "#1abc9c", "width": 0.03},
    {"name": "NH₃", "wavelength": 10.5, "color": "#9b59b6", "width": 0.6},
]


def _get_tsm_scale(radius):
    if radius < 1.5:
        return TSM_SCALE["terran"]
    elif radius < 2.75:
        return TSM_SCALE["super_earth"]
    elif radius < 4.0:
        return TSM_SCALE["sub_neptune"]
    else:
        return TSM_SCALE["giant"]


def compute_tsm(radius, mass, eq_temp, st_radius, j_mag=None):
    """
    Transmission Spectroscopy Metric (Kempton et al. 2018).
    TSM = Scale × (R_p³ × T_eq) / (M_p × R_star²) × 10^(-J_mag/5)
    Higher TSM = easier to characterize atmosphere with JWST.
    """
    if any(v is None or (isinstance(v, float) and np.isnan(v))
           for v in [radius, mass, eq_temp, st_radius]):
        return np.nan

    if mass <= 0 or st_radius <= 0:
        return np.nan

    scale = _get_tsm_scale(radius)
    # Assume J_mag ~ 10 if unknown (typical for Kepler/TESS targets)
    if j_mag is None or np.isnan(j_mag):
        j_mag = 10.0

    tsm = scale * (radius ** 3 * eq_temp) / (mass * st_radius ** 2) * (10 ** (-j_mag / 5.0))
    return tsm


def compute_esm(eq_temp, st_teff, radius, st_radius, j_mag=None):
    """
    Emission Spectroscopy Metric (Kempton et al. 2018).
    ESM = 4.29e6 × (B_7.5(T_day) / B_7.5(T_star)) × (R_p/R_star)² × 10^(-K/5)
    """
    if any(v is None or (isinstance(v, float) and np.isnan(v))
           for v in [eq_temp, st_teff, radius, st_radius]):
        return np.nan

    # Planck function ratio at 7.5 microns (simplified)
    h, c, k_b = 6.626e-34, 3e8, 1.381e-23
    lam = 7.5e-6  # 7.5 microns

    def planck(T):
        if T <= 0:
            return 1e-30
        x = h * c / (lam * k_b * T)
        if x > 500:
            return 1e-30
        return 1.0 / (np.exp(x) - 1.0 + 1e-30)

    t_day = eq_temp * 1.1  # rough day-side temperature
    bp_ratio = planck(t_day) / (planck(st_teff) + 1e-30)

    if j_mag is None or np.isnan(j_mag):
        j_mag = 10.0

    esm = 4.29e6 * bp_ratio * (radius * 6371 / (st_radius * 696340)) ** 2 * 10 ** (-j_mag / 5.0)
    return esm


def score_jwst_feasibility(df):
    """Add TSM, ESM, and JWST priority classification to the dataframe."""
    df = df.copy()

    tsm_vals = []
    esm_vals = []
    for _, row in df.iterrows():
        r = row.get("radius", 1.0)
        m = row.get("estimated_mass", 1.0)
        t = row.get("eq_temp", 300)
        sr = row.get("st_radius", 1.0)
        st = row.get("st_teff", 5780)

        if pd.isna(r): r = 1.0
        if pd.isna(m): m = 1.0
        if pd.isna(t): t = 300
        if pd.isna(sr): sr = 1.0
        if pd.isna(st): st = 5780

        tsm_vals.append(compute_tsm(r, m, t, sr))
        esm_vals.append(compute_esm(t, st, r, sr))

    df["tsm"] = tsm_vals
    df["esm"] = esm_vals

    # JWST priority (Kempton 2018 thresholds)
    df["jwst_priority"] = np.where(
        df["radius"] < 1.5,
        np.where(df["tsm"] > 10, "🟢 High Priority (TSM>10)", "🟡 Moderate"),
        np.where(
            df["radius"] < 2.75,
            np.where(df["tsm"] > 90, "🟢 High Priority (TSM>90)", "🟡 Moderate"),
            np.where(df["tsm"] > 90, "🟢 High Priority", "🟡 Moderate")
        )
    )
    df.loc[df["tsm"].isna(), "jwst_priority"] = "⚪ Insufficient Data"

    return df


def build_synthetic_spectrum(planet_row):
    """
    Generate a synthetic atmospheric transmission spectrum with biosignature markers.
    This simulates what JWST NIRSpec + MIRI would observe during transit.
    """
    wavelength = np.linspace(0.6, 12.0, 600)  # 0.6 to 12 microns

    # Baseline transit depth (Rp/Rs)^2
    rp = planet_row.get("radius", 1.0)
    rs = planet_row.get("st_radius", 1.0)
    if pd.isna(rp): rp = 1.0
    if pd.isna(rs): rs = 1.0

    rp_m = rp * 6.371e6   # Earth radii to meters
    rs_m = rs * 6.96e8    # Solar radii to meters
    baseline_depth = (rp_m / rs_m) ** 2 * 1e6  # in ppm

    # Atmospheric scale height contribution
    temp = planet_row.get("eq_temp", 300)
    if pd.isna(temp): temp = 300
    mass = planet_row.get("estimated_mass", 1.0)
    if pd.isna(mass): mass = 1.0

    # Scale height H = kT / (mu * g)
    g = 9.8 * mass / (rp ** 2 + 1e-6)  # surface gravity
    mu = 28.0  # mean molecular weight (N2 atmosphere)
    k_b = 1.381e-23
    H = k_b * temp / (mu * 1.66e-27 * g + 1e-30)  # meters

    # Number of scale heights visible in transit ~ 5-7
    n_H = 5
    atm_signal = n_H * 2 * rp_m * H / (rs_m ** 2) * 1e6  # ppm

    # Build spectrum with absorption features
    spectrum = np.ones_like(wavelength) * baseline_depth

    in_hz = planet_row.get("in_hz_optimistic", False)

    for bio in BIOSIGNATURES:
        # Gaussian absorption feature
        depth_factor = 1.0
        if bio["name"] in ["O₃ (Ozone)", "O₂", "CH₄ (Methane)"] and in_hz:
            depth_factor = 2.0  # Enhanced for habitable zone planets
        elif bio["name"] == "H₂O" and in_hz:
            depth_factor = 2.5

        feature = atm_signal * depth_factor * np.exp(
            -0.5 * ((wavelength - bio["wavelength"]) / bio["width"]) ** 2
        )
        spectrum += feature

    # Add noise
    noise = np.random.normal(0, atm_signal * 0.15, len(wavelength))
    spectrum += noise

    # Build Plotly figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=wavelength, y=spectrum,
        mode="lines",
        line=dict(color="#70a1ff", width=1.5),
        name="Transit Spectrum",
        hovertemplate="λ = %{x:.2f} μm<br>Depth = %{y:.1f} ppm<extra></extra>",
    ))

    # Mark biosignature absorption bands
    for bio in BIOSIGNATURES:
        y_pos = baseline_depth + atm_signal * 3.5
        fig.add_vrect(
            x0=bio["wavelength"] - bio["width"],
            x1=bio["wavelength"] + bio["width"],
            fillcolor=bio["color"], opacity=0.08,
        )
        fig.add_annotation(
            x=bio["wavelength"], y=y_pos,
            text=f"<b>{bio['name']}</b>",
            showarrow=True, arrowhead=2, arrowcolor=bio["color"],
            font=dict(size=10, color=bio["color"]),
            ax=0, ay=-30,
        )

    # JWST instrument ranges
    fig.add_vrect(x0=0.6, x1=5.3, fillcolor="rgba(52,152,219,0.04)", opacity=1,
                  annotation_text="JWST NIRSpec", annotation_position="top left",
                  annotation_font=dict(size=9, color="#3498db"))
    fig.add_vrect(x0=5.0, x1=12.0, fillcolor="rgba(231,76,60,0.04)", opacity=1,
                  annotation_text="JWST MIRI", annotation_position="top right",
                  annotation_font=dict(size=9, color="#e74c3c"))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(10,10,36,0)",
        plot_bgcolor="rgba(10,10,36,0)",
        title=f"Simulated JWST Transit Spectrum: {planet_row.get('name', 'Unknown')}",
        xaxis_title="Wavelength (μm)",
        yaxis_title="Transit Depth (ppm)",
        height=420,
        margin=dict(l=50, r=30, t=50, b=40),
    )

    return fig
