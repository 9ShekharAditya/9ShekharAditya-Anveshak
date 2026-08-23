"""
science/observatory.py — Indian Observatory Visibility & ISRO Mission Planning.

Computes target visibility from Indian ground-based observatories:
- GMRT (Giant Metrewave Radio Telescope, Pune)
- IAO (Indian Astronomical Observatory, Hanle, Ladakh)
- VBO (Vainu Bappu Observatory, Kavalur, Tamil Nadu)
- ARIES (Aryabhatta Research Institute, Nainital)
- ISRO IDSN (Indian Deep Space Network, Byalalu, Bangalore)
"""

import numpy as np
import pandas as pd


# Indian Observatory Coordinates (lat, lon, altitude_m, name, type)
INDIAN_OBSERVATORIES = {
    "GMRT (Pune)": {
        "lat": 19.0965, "lon": 74.0497, "alt_m": 650,
        "type": "Radio Telescope", "aperture": "30×45m dishes",
        "agency": "NCRA-TIFR",
    },
    "IAO Hanle (Ladakh)": {
        "lat": 32.7794, "lon": 78.9641, "alt_m": 4500,
        "type": "Optical/IR", "aperture": "2.0m HCT",
        "agency": "IIA Bangalore",
    },
    "VBO Kavalur (Tamil Nadu)": {
        "lat": 12.5766, "lon": 78.8266, "alt_m": 725,
        "type": "Optical", "aperture": "2.34m VBT",
        "agency": "IIA Bangalore",
    },
    "ARIES (Nainital)": {
        "lat": 29.3604, "lon": 79.4567, "alt_m": 1951,
        "type": "Optical/IR", "aperture": "3.6m DOT",
        "agency": "ARIES/DST",
    },
    "ISRO IDSN (Byalalu)": {
        "lat": 13.0344, "lon": 77.5116, "alt_m": 900,
        "type": "Deep Space Network", "aperture": "32m + 18m dishes",
        "agency": "ISRO/ISTRAC",
    },
}


def compute_visibility(ra_deg, dec_deg, observatory_lat):
    """
    Compute basic visibility metrics for a target from a given latitude.
    Returns max altitude and hours above 30° elevation per night.
    """
    lat_rad = np.radians(observatory_lat)
    dec_rad = np.radians(dec_deg)

    # Maximum altitude = 90 - |lat - dec|
    max_alt = 90.0 - abs(observatory_lat - dec_deg)

    # Hour angle at 30° elevation
    # sin(30°) = sin(lat)*sin(dec) + cos(lat)*cos(dec)*cos(HA)
    sin_limit = np.sin(np.radians(30.0))
    cos_ha = (sin_limit - np.sin(lat_rad) * np.sin(dec_rad)) / (
        np.cos(lat_rad) * np.cos(dec_rad) + 1e-10
    )

    if abs(cos_ha) > 1.0:
        # Always or never above 30°
        if max_alt >= 30:
            hours_visible = 10.0  # circumpolar-like
        else:
            hours_visible = 0.0
    else:
        ha_rad = np.arccos(np.clip(cos_ha, -1, 1))
        hours_visible = 2.0 * np.degrees(ha_rad) / 15.0  # convert degrees to hours

    is_observable = max_alt >= 30.0 and hours_visible >= 1.0
    quality = "Excellent" if max_alt >= 60 else ("Good" if max_alt >= 45 else ("Fair" if max_alt >= 30 else "Below Horizon"))

    return {
        "max_altitude_deg": round(max_alt, 1),
        "hours_above_30deg": round(hours_visible, 1),
        "observable": is_observable,
        "quality": quality,
    }


def get_visibility_table(dec_deg, ra_deg=None):
    """
    Compute visibility of a target from all Indian observatories.
    Returns a DataFrame with one row per observatory.
    """
    rows = []
    for name, obs in INDIAN_OBSERVATORIES.items():
        vis = compute_visibility(ra_deg or 0, dec_deg, obs["lat"])
        rows.append({
            "Observatory": name,
            "Agency": obs["agency"],
            "Type": obs["type"],
            "Aperture": obs["aperture"],
            "Latitude": f"{obs['lat']:.2f}°N",
            "Altitude (m)": obs["alt_m"],
            "Max Elevation (°)": vis["max_altitude_deg"],
            "Hours Visible (>30°)": vis["hours_above_30deg"],
            "Observable": "✅ Yes" if vis["observable"] else "❌ No",
            "Quality": vis["quality"],
        })
    return pd.DataFrame(rows)
