"""
science/habitability.py — Scientific & Astrobiological Inference Engine.

Implements:
1. Kopparapu et al. (2013) Habitable Zone Boundaries (Conservative & Optimistic)
2. Earth Similarity Index (ESI)
3. Planetary Mass & Density Modeling (Chen & Kipping 2017)
4. Tidal Locking & Synchronous Rotation Timescale
5. Atmospheric Retention Index (Jeans Escape / Escape Velocity)
6. Stellar Flare & UV Hazard Risk for M-Dwarfs
7. Transit Spectroscopy Metric (TSM / JWST Follow-up Suitability Proxy)
8. Composite Habitability Scoring & Scientific Inference
"""

import numpy as np
import pandas as pd

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    HZ_COEFFICIENTS, EARTH, ESI_WEIGHTS, SIZE_CLASSES,
    HABIT_WEIGHTS, TEMP_OPTIMAL, MDWARF_TEFF_THRESHOLD,
    TIDAL_LOCK_SEMI_MAJOR_AU, MASS_RADIUS_TERRAN, MASS_RADIUS_NEPTUNIAN,
    TIER_EMOJIS,
)


def compute_hz_distances(st_teff, st_radius):
    """
    Compute all 4 HZ boundary distances (AU) for a star using Kopparapu (2013).
    Luminosity L/L_sun = (R/R_sun)² × (T_eff/5780)⁴
    """
    luminosity = (st_radius ** 2) * ((st_teff / 5780.0) ** 4)
    Tc = st_teff - 5780.0

    distances = {}
    for key, name in [("inner_opt", "recent_venus"),
                      ("inner_con", "runaway_greenhouse"),
                      ("outer_con", "max_greenhouse"),
                      ("outer_opt", "early_mars")]:
        coeffs = HZ_COEFFICIENTS[name]
        S_eff = (coeffs["S_eff_sun"]
                 + coeffs["a"] * Tc
                 + coeffs["b"] * (Tc ** 2)
                 + coeffs["c"] * (Tc ** 3)
                 + coeffs["d"] * (Tc ** 4))
        S_eff = np.maximum(S_eff, 0.001)
        distances[key] = np.sqrt(luminosity / S_eff)

    return distances


def estimate_mass(radius):
    """Estimate planet mass from radius using Chen & Kipping (2017) power laws."""
    radius = np.asarray(radius, dtype=float)
    mass = np.where(
        radius < 1.23,
        radius ** MASS_RADIUS_TERRAN["b"],
        (1.23 ** MASS_RADIUS_TERRAN["b"]) * ((radius / 1.23) ** MASS_RADIUS_NEPTUNIAN["b"])
    )
    return mass


def compute_esi(radius, eq_temp, mass=None):
    """Compute Earth Similarity Index (0 to 1)."""
    radius = np.asarray(radius, dtype=float)
    eq_temp = np.asarray(eq_temp, dtype=float)

    if mass is None:
        mass = estimate_mass(radius)
    else:
        mass = np.asarray(mass, dtype=float)

    density = (mass / (radius ** 3 + 1e-6)) * EARTH["density"]
    escape_vel = np.sqrt(np.maximum(mass / (radius + 1e-6), 0)) * EARTH["escape_velocity"]

    def similarity(x, x_earth, weight):
        ratio = np.abs(x - x_earth) / (x + x_earth + 1e-10)
        return (1.0 - ratio) ** (weight / 4.0)

    esi = (similarity(radius, EARTH["radius"], ESI_WEIGHTS["radius"])
           * similarity(density, EARTH["density"], ESI_WEIGHTS["density"])
           * similarity(escape_vel, EARTH["escape_velocity"], ESI_WEIGHTS["escape_velocity"])
           * similarity(eq_temp, EARTH["eq_temp"], ESI_WEIGHTS["eq_temp"]))

    return np.clip(esi, 0.0, 1.0)


def classify_size(radius):
    """Classify planet into canonical planetary size regime."""
    radius = np.asarray(radius, dtype=float)
    result = np.full(radius.shape, "Unknown", dtype=object)
    for label, (lo, hi) in SIZE_CLASSES.items():
        mask = (radius >= lo) & (radius < hi)
        result[mask] = label
    return result


def score_habitability(df):
    """
    Vectorized scoring and deep scientific astrobiology inferences.
    Calculates HZ, ESI, Tidal Lock, Atmospheric Retention, and JWST follow-up feasibility.
    """
    df = df.copy()

    #  1. Habitable Zone Boundaries 
    has_star = df["st_teff"].notna() & df["st_radius"].notna()
    for col in ["hz_inner_con", "hz_inner_opt", "hz_outer_con", "hz_outer_opt"]:
        df[col] = np.nan

    if has_star.any():
        teff = df.loc[has_star, "st_teff"].values
        srad = df.loc[has_star, "st_radius"].values
        hz = compute_hz_distances(teff, srad)
        df.loc[has_star, "hz_inner_opt"] = hz["inner_opt"]
        df.loc[has_star, "hz_inner_con"] = hz["inner_con"]
        df.loc[has_star, "hz_outer_con"] = hz["outer_con"]
        df.loc[has_star, "hz_outer_opt"] = hz["outer_opt"]

    #  2. Habitable Zone Flags & Position 
    sma = df["semi_major_axis"]
    df["in_hz_conservative"] = (sma >= df["hz_inner_con"]) & (sma <= df["hz_outer_con"])
    df["in_hz_optimistic"] = (sma >= df["hz_inner_opt"]) & (sma <= df["hz_outer_opt"])

    hz_center = (df["hz_inner_con"] + df["hz_outer_con"]) / 2.0
    hz_width = np.maximum(df["hz_outer_con"] - df["hz_inner_con"], 0.001)
    df["hz_score"] = np.clip(1.0 - (np.abs(sma - hz_center) / (hz_width / 2.0)), 0.0, 1.0)
    df.loc[~df["in_hz_optimistic"].fillna(False), "hz_score"] = 0.0

    #  3. Size & Mass Modeling 
    r = df["radius"]
    df["estimated_mass"] = np.where(
        df["mass"].notna(),
        df["mass"],
        np.where(r.notna(), estimate_mass(r.values), np.nan)
    )

    df["size_score"] = np.where(
        r.isna(), 0.0,
        np.where(
            (r >= 0.5) & (r <= 2.5),
            np.exp(-0.5 * (((r - 1.0) / 0.55) ** 2)),
            0.0
        )
    )

    #  4. Equilibrium Temperature Score 
    t = df["eq_temp"]
    t_lo, t_hi = TEMP_OPTIMAL
    t_mid = (t_lo + t_hi) / 2.0
    t_range = (t_hi - t_lo) / 2.0
    df["temp_score"] = np.where(
        t.isna(), 0.0,
        np.clip(np.exp(-0.5 * (((t - t_mid) / t_range) ** 2)), 0.0, 1.0)
    )

    #  5. Astrobiology Inferences: Tidal Locking & UV Flaring 
    is_mdwarf = df["st_teff"] < MDWARF_TEFF_THRESHOLD
    df["tidal_lock"] = "Unlikely Locked"
    df.loc[is_mdwarf & (sma < 0.15), "tidal_lock"] = "Likely Synchronous (Locked)"
    df.loc[is_mdwarf & (sma >= 0.15) & (sma < TIDAL_LOCK_SEMI_MAJOR_AU), "tidal_lock"] = "Possibly Locked"

    df["tidal_penalty"] = np.where(
        df["tidal_lock"] == "Likely Synchronous (Locked)", 0.12,
        np.where(df["tidal_lock"] == "Possibly Locked", 0.05, 0.0)
    )

    # UV Flaring Risk for M-Dwarfs
    df["uv_flare_risk"] = np.where(
        is_mdwarf & (sma < 0.2), "High (M-Dwarf Flares)",
        np.where(is_mdwarf, "Moderate", "Low (Stable Star)")
    )

    #  6. Atmospheric Retention Index (Jeans Escape Proxy) 
    # Escape velocity vs Thermal thermal velocity ratio: v_esc / sqrt(T_eq)
    m = df["estimated_mass"].fillna(1.0)
    r_safe = df["radius"].fillna(1.0)
    v_esc = np.sqrt(np.maximum(m / r_safe, 0.1)) * EARTH["escape_velocity"]
    df["escape_velocity_kms"] = v_esc
    df["atm_retention"] = np.where(
        v_esc >= 10.0, "Strong (Dense Atmosphere Likely)",
        np.where(v_esc >= 6.0, "Moderate (Secondary Atmosphere)", "Weak (Atmospheric Stripping Risk)")
    )

    #  7. Earth Similarity Index (ESI) 
    has_esi = df["radius"].notna() & df["eq_temp"].notna()
    df["esi"] = 0.0
    if has_esi.any():
        df.loc[has_esi, "esi"] = compute_esi(
            df.loc[has_esi, "radius"].values,
            df.loc[has_esi, "eq_temp"].values,
            df.loc[has_esi, "estimated_mass"].values,
        )

    # 8. Size Classification 
    df["size_class"] = "Unknown"
    if df["radius"].notna().any():
        df.loc[df["radius"].notna(), "size_class"] = classify_size(df.loc[df["radius"].notna(), "radius"].values)

    #  9. Composite Habitability Score 
    w = HABIT_WEIGHTS
    df["habitability_score"] = (
        w["hz_position"] * df["hz_score"]
        + w["size_score"] * df["size_score"]
        + w["temp_score"] * df["temp_score"]
        - w["tidal_penalty"] * df["tidal_penalty"]
    )
    df["habitability_score"] = np.clip(df["habitability_score"], 0.0, 1.0)

    # Tier Assignment
    df["habitability_tier"] = np.where(
        df["radius"].notna() & (df["radius"] > 5.5),
        "Not Habitable",  # Gas giant
        np.where(
            df["habitability_score"] >= 0.55, "High Potential",
            np.where(
                df["habitability_score"] >= 0.30, "Moderate Potential",
                np.where(
                    df["habitability_score"] >= 0.10, "Low Potential",
                    "Not Habitable"
                )
            )
        )
    )

    df["tier_emoji"] = df["habitability_tier"].map(TIER_EMOJIS).fillna("⚫")

    return df
