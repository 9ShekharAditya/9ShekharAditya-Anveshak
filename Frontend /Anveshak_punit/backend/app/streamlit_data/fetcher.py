"""
data/fetcher.py — Telescope Ingestion Registry & Data Pipeline.

Uses the `BaseTelescopeAdapter` plugin architecture to dynamically load
data from all registered space telescope missions and apply Kepler's 3rd Law
where orbital distance is unmeasured.
"""

import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .adapters import (
    KeplerAdapter, TessAdapter, K2Adapter, ConfirmedPlanetsAdapter
)

# Registry of active space telescope adapters
TELESCOPE_REGISTRY = [
    KeplerAdapter(),
    TessAdapter(),
    K2Adapter(),
    ConfirmedPlanetsAdapter(),
]


def register_telescope_adapter(adapter):
    """Dynamically register a new space telescope adapter at runtime."""
    TELESCOPE_REGISTRY.append(adapter)


def get_unified_candidates(include_confirmed: bool = True) -> pd.DataFrame:
    """
    Ingest from all registered telescope adapters, standardize schemas,
    and compute missing orbital distances via Kepler's 3rd Law.
    """
    frames = []

    for adapter in TELESCOPE_REGISTRY:
        if not include_confirmed and adapter.mission_name == "Confirmed":
            continue
        try:
            df = adapter.fetch(use_cache=True)
            frames.append(df)
        except Exception as e:
            print(f"⚠ [{adapter.mission_name}] Ingestion notice: {e}")

    if not frames:
        raise RuntimeError("No telescope datasets could be loaded from NASA TAP service.")

    unified = pd.concat(frames, ignore_index=True)

    numeric_cols = ["period", "radius", "mass", "insol", "eq_temp",
                    "semi_major_axis", "eccentricity", "inclination",
                    "st_teff", "st_radius", "st_mass"]
    for col in numeric_cols:
        unified[col] = pd.to_numeric(unified[col], errors="coerce")

    # ── Kepler's 3rd Law Calculation for Missing Distances ───────────
    # a (AU) = [ (M_star / M_sun) * (Period / 365.25 days)^2 ]^(1/3)
    missing_sma = unified["semi_major_axis"].isna() & unified["period"].notna()
    if missing_sma.any():
        m_star = unified.loc[missing_sma, "st_mass"].fillna(1.0)
        t_yr = unified.loc[missing_sma, "period"] / 365.25
        unified.loc[missing_sma, "semi_major_axis"] = (m_star * (t_yr ** 2)) ** (1.0 / 3.0)

    return unified
