"""
config.py — All constants, API URLs, and scientific coefficients in one place.

WHY a separate config file?
Instead of scattering magic numbers throughout the code,
we put them all here. If NASA changes their URL or a scientific
paper updates a coefficient, you change ONE file.
"""

# ─── NASA Exoplanet Archive TAP API ───────────────────────────────────
TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

# Cache settings
CACHE_DIR = "data/cache"
CACHE_TTL_HOURS = 24  # re-fetch data if cache is older than this

# ─── Habitable Zone Coefficients (Kopparapu et al. 2013) ─────────────
# Each boundary has: S_eff_sun, a, b, c, d
# Formula: S_eff = S_eff_sun + a*Tc + b*Tc^2 + c*Tc^3 + d*Tc^4
# where Tc = T_eff_star - 5780
HZ_COEFFICIENTS = {
    "recent_venus": {
        "label": "Recent Venus (Optimistic Inner)",
        "S_eff_sun": 1.7763,
        "a": 1.4335e-4,
        "b": 3.3954e-9,
        "c": -7.6364e-12,
        "d": -1.1950e-15,
    },
    "runaway_greenhouse": {
        "label": "Runaway Greenhouse (Conservative Inner)",
        "S_eff_sun": 1.0385,
        "a": 1.2456e-4,
        "b": 1.4612e-8,
        "c": -7.6345e-12,
        "d": -1.7511e-15,
    },
    "max_greenhouse": {
        "label": "Maximum Greenhouse (Conservative Outer)",
        "S_eff_sun": 0.3507,
        "a": 5.9578e-5,
        "b": 1.6707e-9,
        "c": -3.0058e-12,
        "d": -5.1925e-16,
    },
    "early_mars": {
        "label": "Early Mars (Optimistic Outer)",
        "S_eff_sun": 0.3207,
        "a": 5.4471e-5,
        "b": 1.5275e-9,
        "c": -2.1709e-12,
        "d": -3.8282e-16,
    },
}

# ─── Earth Similarity Index (ESI) Reference Values ───────────────────
# These are Earth's values — we compare every candidate against these
EARTH = {
    "radius": 1.0,          # Earth radii
    "density": 5.51,         # g/cm³
    "escape_velocity": 11.2, # km/s
    "eq_temp": 255.0,        # Kelvin (effective radiative temperature)
}

# ESI weights (all equal in the standard formulation)
ESI_WEIGHTS = {
    "radius": 0.57,
    "density": 1.07,
    "escape_velocity": 0.70,
    "eq_temp": 5.58,
}

# ─── Planet Classification Thresholds ─────────────────────────────────
# Based on radius in Earth radii
SIZE_CLASSES = {
    "Sub-Earth":     (0.0,  0.8),
    "Earth-sized":   (0.8,  1.25),
    "Super-Earth":   (1.25, 2.0),
    "Sub-Neptune":   (2.0,  4.0),
    "Neptune-sized": (4.0,  6.0),
    "Sub-Jupiter":   (6.0,  11.0),
    "Jupiter-sized": (11.0, float("inf")),
}

# ─── Habitability Scoring Weights ────────────────────────────────────
HABIT_WEIGHTS = {
    "hz_position": 0.35,   # how centered in habitable zone
    "size_score": 0.25,    # penalty for being too big/small
    "temp_score": 0.25,    # equilibrium temperature suitability
    "tidal_penalty": 0.15, # reduction for likely tidally locked
}

# Optimal temperature range for habitability scoring (Kelvin)
TEMP_OPTIMAL = (200, 320)

# ─── Tidal Locking ───────────────────────────────────────────────────
# Stars cooler than this are M-dwarfs where tidal locking matters
MDWARF_TEFF_THRESHOLD = 3700  # Kelvin
TIDAL_LOCK_SEMI_MAJOR_AU = 0.5  # approximate tidal lock radius for M-dwarfs

# ─── Mass-Radius Relation (Chen & Kipping 2017, simplified) ─────────
# Used to ESTIMATE mass when not measured
# log10(M) = a + b * log10(R)  (in Earth units)
MASS_RADIUS_TERRAN = {"a": 0.0, "b": 3.268}     # R < 1.23 R_earth
MASS_RADIUS_NEPTUNIAN = {"a": 0.0, "b": 1.70}    # 1.23 < R < 14.26 R_earth

# ─── Display Settings ────────────────────────────────────────────────
TIER_COLORS = {
    "High Potential": "#2ecc71",      # green
    "Moderate Potential": "#f1c40f",   # yellow
    "Low Potential": "#e74c3c",        # red
    "Not Habitable": "#95a5a6",        # gray
}

TIER_EMOJIS = {
    "High Potential": "🟢",
    "Moderate Potential": "🟡",
    "Low Potential": "🔴",
    "Not Habitable": "⚫",
}

SOURCE_COLORS = {
    "Kepler": "#3498db",
    "K2": "#9b59b6",
    "TESS": "#e67e22",
    "Confirmed": "#2ecc71",
}
