"""
data/adapters.py — Extensible Telescope Adapter Framework.

Allows adding ANY past, present, or future space telescope mission
(e.g., Kepler, TESS, K2, PLATO, Nancy Grace Roman, Ariel, HWO, CHEOPS)
by simply subclassing `BaseTelescopeAdapter`.
"""

import os
import requests
import pandas as pd
from io import StringIO
from abc import ABC, abstractmethod
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TAP_URL, CACHE_DIR, CACHE_TTL_HOURS


class BaseTelescopeAdapter(ABC):
    """
    Abstract Base Class for Space Telescope Data Ingestion.
    Subclass this to add any new telescope or data pipeline.
    """
    mission_name: str = "Unknown Mission"
    cache_filename: str = "mission_data"

    def __init__(self, tap_url: str = TAP_URL):
        self.tap_url = tap_url

    @abstractmethod
    def get_query(self) -> str:
        """Return the TAP SQL query to fetch this telescope's candidates."""
        pass

    @abstractmethod
    def standardize(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Map raw telescope column names to the standardized schema."""
        pass

    # Required columns in the standardized schema
    REQUIRED_COLUMNS = {"name", "host_name", "source", "period", "radius", "eq_temp", "semi_major_axis"}

    def fetch(self, use_cache: bool = True) -> pd.DataFrame:
        """Fetch data from TAP API with local parquet caching, TTL, and schema validation."""
        import time
        Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
        cache_path = os.path.join(CACHE_DIR, f"{self.cache_filename}.parquet")

        if use_cache and os.path.exists(cache_path):
            # Check TTL
            age_hours = (time.time() - os.path.getmtime(cache_path)) / 3600
            if age_hours < CACHE_TTL_HOURS:
                cached_df = pd.read_parquet(cache_path)
                # Validate schema — if old cache has raw columns, invalidate it
                if self.REQUIRED_COLUMNS.issubset(set(cached_df.columns)):
                    return cached_df
                else:
                    print(f"[{self.mission_name}] Cache schema mismatch — re-fetching from NASA TAP...")

        query = self.get_query()
        response = requests.get(self.tap_url, params={"query": query, "format": "csv"}, timeout=120)
        if response.status_code != 200:
            raise ConnectionError(f"[{self.mission_name}] NASA TAP query failed: {response.text[:200]}")

        raw_df = pd.read_csv(StringIO(response.text))
        raw_df["source"] = self.mission_name
        std_df = self.standardize(raw_df)

        std_df.to_parquet(cache_path, index=False)
        return std_df


# ─── Concrete Telescope Adapters ─────────────────────────────────────

class KeplerAdapter(BaseTelescopeAdapter):
    mission_name = "Kepler"
    cache_filename = "kepler_candidates"

    def get_query(self) -> str:
        return """
        SELECT kepid, kepoi_name, koi_disposition, koi_period, koi_prad,
               koi_insol, koi_teq, koi_eccen, koi_incl, koi_sma,
               koi_steff, koi_srad, koi_smass
        FROM cumulative
        WHERE koi_disposition = 'CANDIDATE'
        """

    def standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            "name": df["kepoi_name"],
            "host_name": df["kepid"].astype(str),
            "source": self.mission_name,
            "disposition": df["koi_disposition"],
            "period": df["koi_period"],
            "radius": df["koi_prad"],
            "mass": pd.NA,
            "insol": df["koi_insol"],
            "eq_temp": df["koi_teq"],
            "semi_major_axis": df["koi_sma"],
            "eccentricity": df["koi_eccen"],
            "inclination": df["koi_incl"],
            "st_teff": df["koi_steff"],
            "st_radius": df["koi_srad"],
            "st_mass": df["koi_smass"],
        })


class TessAdapter(BaseTelescopeAdapter):
    mission_name = "TESS"
    cache_filename = "toi_candidates"

    def get_query(self) -> str:
        return """
        SELECT toi, toipfx, tfopwg_disp, pl_orbper, pl_rade, pl_insol,
               pl_eqt, pl_orbsmax, pl_orbeccen, pl_orbincl,
               st_teff, st_rad, st_mass
        FROM toi
        WHERE tfopwg_disp = 'PC'
        """

    def standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            "name": df["toi"].astype(str),
            "host_name": df["toipfx"].astype(str),
            "source": self.mission_name,
            "disposition": df["tfopwg_disp"],
            "period": df["pl_orbper"],
            "radius": df["pl_rade"],
            "mass": pd.NA,
            "insol": df["pl_insol"],
            "eq_temp": df["pl_eqt"],
            "semi_major_axis": df["pl_orbsmax"],
            "eccentricity": df["pl_orbeccen"],
            "inclination": df["pl_orbincl"],
            "st_teff": df["st_teff"],
            "st_radius": df["st_rad"],
            "st_mass": df["st_mass"],
        })


class K2Adapter(BaseTelescopeAdapter):
    mission_name = "K2"
    cache_filename = "k2_candidates"

    def get_query(self) -> str:
        return """
        SELECT pl_name, hostname, disposition, pl_orbper, pl_rade, pl_bmasse,
               pl_insol, pl_eqt, pl_orbsmax, pl_orbeccen, pl_orbincl,
               st_teff, st_rad, st_mass
        FROM k2pandc
        WHERE disposition = 'CANDIDATE'
        """

    def standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            "name": df["pl_name"],
            "host_name": df["hostname"],
            "source": self.mission_name,
            "disposition": df["disposition"],
            "period": df["pl_orbper"],
            "radius": df["pl_rade"],
            "mass": df["pl_bmasse"],
            "insol": df["pl_insol"],
            "eq_temp": df["pl_eqt"],
            "semi_major_axis": df["pl_orbsmax"],
            "eccentricity": df["pl_orbeccen"],
            "inclination": df["pl_orbincl"],
            "st_teff": df["st_teff"],
            "st_radius": df["st_rad"],
            "st_mass": df["st_mass"],
        })


class ConfirmedPlanetsAdapter(BaseTelescopeAdapter):
    mission_name = "Confirmed"
    cache_filename = "confirmed_planets"

    def get_query(self) -> str:
        return """
        SELECT pl_name, hostname, pl_orbper, pl_rade, pl_bmasse, pl_insol,
               pl_eqt, pl_orbsmax, pl_orbeccen, pl_orbincl,
               st_teff, st_rad, st_mass
        FROM pscomppars
        """

    def standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            "name": df["pl_name"],
            "host_name": df["hostname"],
            "source": self.mission_name,
            "disposition": "CONFIRMED",
            "period": df["pl_orbper"],
            "radius": df["pl_rade"],
            "mass": df["pl_bmasse"],
            "insol": df["pl_insol"],
            "eq_temp": df["pl_eqt"],
            "semi_major_axis": df["pl_orbsmax"],
            "eccentricity": df["pl_orbeccen"],
            "inclination": df["pl_orbincl"],
            "st_teff": df["st_teff"],
            "st_radius": df["st_rad"],
            "st_mass": df["st_mass"],
        })


# ─── Future Space Telescope Adapter Template ─────────────────────────
class FutureMissionAdapterTemplate(BaseTelescopeAdapter):
    """
    Template for adding upcoming missions (e.g. ESA PLATO, NASA Nancy Grace Roman, Ariel).
    To activate a new telescope:
    1. Set `mission_name` and `cache_filename`
    2. Define `get_query()`
    3. Define `standardize()` mapping
    4. Add to `TELESCOPE_REGISTRY` in data/fetcher.py
    """
    mission_name = "Future Mission"
    cache_filename = "future_candidates"

    def get_query(self) -> str:
        return "SELECT * FROM future_table WHERE disposition = 'CANDIDATE'"

    def standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            "name": df.get("name", "Unknown"),
            "host_name": df.get("host_name", "Unknown"),
            "source": self.mission_name,
            "disposition": "CANDIDATE",
            "period": df.get("period"),
            "radius": df.get("radius"),
            "mass": df.get("mass", pd.NA),
            "insol": df.get("insol"),
            "eq_temp": df.get("eq_temp"),
            "semi_major_axis": df.get("semi_major_axis"),
            "eccentricity": df.get("eccentricity", 0.0),
            "inclination": df.get("inclination", 90.0),
            "st_teff": df.get("st_teff"),
            "st_radius": df.get("st_radius"),
            "st_mass": df.get("st_mass"),
        })
