from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

from app.services.science.spectroscopy import compute_tsm, compute_esm, build_synthetic_spectrum
from app.services.science.observatory import get_visibility_table

router = APIRouter()

class TransitRequest(BaseModel):
    name: str = "Unknown Planet"
    radius: float
    st_radius: float
    eq_temp: float = 300.0
    estimated_mass: float = 1.0
    in_hz_optimistic: bool = False

@router.post("/transit-spectrum")
def get_transit_spectrum(req: TransitRequest):
    try:
        planet_row = req.model_dump()
        fig = build_synthetic_spectrum(planet_row)
        return json.loads(fig.to_json())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MetricsRequest(BaseModel):
    planet_radius: float
    planet_mass: Optional[float] = None
    star_radius: float
    star_teff: float
    j_mag: float
    k_mag: float

@router.post("/metrics")
def get_science_metrics(req: MetricsRequest):
    tsm = compute_tsm(req.planet_radius, req.planet_mass, req.star_radius, req.star_teff, req.j_mag)
    esm = compute_esm(req.planet_radius, req.star_teff, req.k_mag)
    return {"tsm": tsm, "esm": esm}

class VisibilityRequest(BaseModel):
    ra: float
    dec: float

@router.post("/observability")
def get_observability(req: VisibilityRequest):
    df = get_visibility_table(req.dec, req.ra)
    return df.to_dict(orient="records")

import pandas as pd
import numpy as np

from app.streamlit_data.fetcher import get_unified_candidates
from app.services.science.habitability import score_habitability

@router.get("/candidates")
async def get_habitable_candidates():
    # Use exact Streamlit data engine!
    raw_df = get_unified_candidates(include_confirmed=True)
    scored_df = score_habitability(raw_df)
    
    scored_df = scored_df.sort_values(by="habitability_score", ascending=False)
    
    candidates_list = []
    
    for idx, row in scored_df.iterrows():
        hz_inner_con = float(row.get('hz_inner_con', 0.95)) if pd.notna(row.get('hz_inner_con')) else 0.95
        hz_outer_con = float(row.get('hz_outer_con', 1.37)) if pd.notna(row.get('hz_outer_con')) else 1.37
        hz_inner_opt = float(row.get('hz_inner_opt', 0.75)) if pd.notna(row.get('hz_inner_opt')) else 0.75
        hz_outer_opt = float(row.get('hz_outer_opt', 1.77)) if pd.notna(row.get('hz_outer_opt')) else 1.77
        orbsmax = float(row.get('semi_major_axis', 1.0)) if pd.notna(row.get('semi_major_axis')) else 1.0
        in_hz = bool(row.get('in_hz_conservative', False)) or (hz_inner_con <= orbsmax <= hz_outer_con)
        
        pl_rade = float(row.get('radius', 1.0)) if pd.notna(row.get('radius')) else 1.0
        pl_masse = float(row.get('mass', 1.0)) if pd.notna(row.get('mass')) else 1.0
        pl_orbper = float(row.get('period', 365.25)) if pd.notna(row.get('period')) else 365.25
        pl_eqt = float(row.get('eq_temp', 255.0)) if pd.notna(row.get('eq_temp')) else 255.0
        st_teff = float(row.get('st_teff', 5778.0)) if pd.notna(row.get('st_teff')) else 5778.0
        st_rad = float(row.get('st_radius', 1.0)) if pd.notna(row.get('st_radius')) else 1.0
        pl_insol = float(row.get('insol', 1.0)) if pd.notna(row.get('insol')) else 1.0
        pl_name = str(row.get('name', 'Unknown'))
        pl_id = pl_name.lower().replace(' ', '-') + str(idx) # ensure unique ID

        candidates_list.append({
            "id": pl_id,
            "name": pl_name,
            "system": str(row.get('host_name', '')),
            "discoveryMethod": str(row.get('source', 'Unknown')),
            "discoveryYear": 2000,
            "radius": pl_rade,
            "mass": pl_masse,
            "orbitalDistance": orbsmax,
            "orbitalPeriod": pl_orbper,
            "equilibriumTemp": pl_eqt,
            "stellarTemp": st_teff,
            "stellarRadius": st_rad,
            "hzInnerCon": hz_inner_con,
            "hzOuterCon": hz_outer_con,
            "hzInnerOpt": hz_inner_opt,
            "hzOuterOpt": hz_outer_opt,
            "inHz": in_hz,
            "score": float(row.get('habitability_score', 0)),
            "habitabilityClass": "Psychroplanet" if pl_eqt < 250 else "Mesoplanet" if pl_eqt < 300 else "Thermoplanet",
            "planetImage": "/assets/placeholder-planet.png",
            # Fields for Overview and CandidatesList
            "planet": pl_name,
            "mission": str(row.get('source', 'Unknown')),
            "temp": pl_eqt,
            "period": pl_orbper,
            "insol": pl_insol,
            "esi": float(row.get('esi', 0.0)) if pd.notna(row.get('esi')) else 0.0,
            "sizeClass": str(row.get('size_class', 'Unknown')),
            "tidalLock": str(row.get('tidal_lock', 'Unknown')),
            "tier": str(row.get('habitability_tier', 'Unknown'))
        })
        
    return {"candidates": candidates_list, "total": len(candidates_list)}







@router.get("/systems")
async def get_3d_systems():
    """
    Returns multi-planet systems with Keplerian orbital parameters,
    Habitable Zone boundaries (Kopparapu 2013), and astrobiology metrics.
    """
    systems = [
        {
            "id": "trappist-1",
            "title": "TRAPPIST-1 (Host Star + Habitable Zone + Orbits)",
            "starName": "TRAPPIST-1",
            "st_teff": 2566.0,
            "st_radius": 0.121,
            "st_mass": 0.089,
            "spectralType": "M-Dwarf (Ultra-Cool Red)",
            "starColor": "#ff3f34",
            "hzInnerRadius": 0.022,
            "hzOuterRadius": 0.048,
            "nasaEyesUrl": "https://eyes.nasa.gov/apps/exo/#/star/TRAPPIST-1",
            "planets": [
                {
                    "id": "trappist-1-b",
                    "name": "TRAPPIST-1 b",
                    "sma": 0.0115,
                    "ecc": 0.006,
                    "period": 1.51,
                    "radius": 1.116,
                    "mass": 1.374,
                    "temp": 398.0,
                    "insol": 4.25,
                    "esi": 0.696,
                    "score": 0.245,
                    "inHz": False,
                    "status": "CONFIRMED",
                    "color": "#ef4444",
                    "climate": "Scorched / Super-Venus (398K)",
                    "atmRetention": "Dense CO2 Atmosphere Likely",
                    "tidalLock": "Tidally Locked (Synchronous)",
                    "uvHazard": "High (M-Dwarf Flares)",
                    "discoveryMethod": "Transit",
                    "discoveryYear": 2016
                },
                {
                    "id": "trappist-1-c",
                    "name": "TRAPPIST-1 c",
                    "sma": 0.0158,
                    "ecc": 0.007,
                    "period": 2.42,
                    "radius": 1.097,
                    "mass": 1.308,
                    "temp": 342.0,
                    "insol": 2.27,
                    "esi": 0.702,
                    "score": 0.380,
                    "inHz": False,
                    "status": "CONFIRMED",
                    "color": "#f59e0b",
                    "climate": "Hot Terrestrial / Venus Analog",
                    "atmRetention": "Strong (Thick Atmosphere)",
                    "tidalLock": "Tidally Locked (Synchronous)",
                    "uvHazard": "High (M-Dwarf Flares)",
                    "discoveryMethod": "Transit",
                    "discoveryYear": 2016
                },
                {
                    "id": "trappist-1-d",
                    "name": "TRAPPIST-1 d",
                    "sma": 0.0223,
                    "ecc": 0.007,
                    "period": 4.05,
                    "radius": 0.788,
                    "mass": 0.388,
                    "temp": 288.0,
                    "insol": 1.14,
                    "esi": 0.902,
                    "score": 0.710,
                    "inHz": True,
                    "status": "CONFIRMED",
                    "color": "#10b981",
                    "climate": "Warm Coastal / Temperate (288K)",
                    "atmRetention": "Moderate (Volatiles Capable)",
                    "tidalLock": "Tidally Locked (Eyeball Climate)",
                    "uvHazard": "Moderate (M-Dwarf Flares)",
                    "discoveryMethod": "Transit",
                    "discoveryYear": 2016
                },
                {
                    "id": "trappist-1-e",
                    "name": "TRAPPIST-1 e",
                    "sma": 0.0293,
                    "ecc": 0.005,
                    "period": 6.10,
                    "radius": 0.920,
                    "mass": 0.692,
                    "temp": 251.0,
                    "insol": 0.66,
                    "esi": 0.850,
                    "score": 0.850,
                    "inHz": True,
                    "status": "CONFIRMED",
                    "color": "#2ed573",
                    "climate": "Earth-Analogue (Liquid Water Oceans)",
                    "atmRetention": "Optimal (Surface Water & Atmosphere Capable)",
                    "tidalLock": "Tidally Locked (Temperate Day-Side)",
                    "uvHazard": "Moderate (M-Dwarf Flares)",
                    "discoveryMethod": "Transit",
                    "discoveryYear": 2017
                },
                {
                    "id": "trappist-1-f",
                    "name": "TRAPPIST-1 f",
                    "sma": 0.0385,
                    "ecc": 0.010,
                    "period": 9.21,
                    "radius": 1.045,
                    "mass": 1.039,
                    "temp": 219.0,
                    "insol": 0.38,
                    "esi": 0.701,
                    "score": 0.760,
                    "inHz": True,
                    "status": "CONFIRMED",
                    "color": "#2ed573",
                    "climate": "Cool Earth / Ocean-Ice World",
                    "atmRetention": "Strong (Global Volatile Envelope)",
                    "tidalLock": "Tidally Locked",
                    "uvHazard": "Low",
                    "discoveryMethod": "Transit",
                    "discoveryYear": 2017
                },
                {
                    "id": "trappist-1-g",
                    "name": "TRAPPIST-1 g",
                    "sma": 0.0468,
                    "ecc": 0.002,
                    "period": 12.35,
                    "radius": 1.129,
                    "mass": 1.321,
                    "temp": 198.0,
                    "insol": 0.26,
                    "esi": 0.588,
                    "score": 0.640,
                    "inHz": True,
                    "status": "CONFIRMED",
                    "color": "#00d2d3",
                    "climate": "Cold Terrestrial / Outer HZ Edge",
                    "atmRetention": "Strong (Thick CO2/H2O Blanket Required)",
                    "tidalLock": "Tidally Locked",
                    "uvHazard": "Low",
                    "discoveryMethod": "Transit",
                    "discoveryYear": 2017
                },
                {
                    "id": "trappist-1-h",
                    "name": "TRAPPIST-1 h",
                    "sma": 0.0619,
                    "ecc": 0.006,
                    "period": 18.77,
                    "radius": 0.775,
                    "mass": 0.326,
                    "temp": 173.0,
                    "insol": 0.15,
                    "esi": 0.463,
                    "score": 0.290,
                    "inHz": False,
                    "status": "CONFIRMED",
                    "color": "#74b9ff",
                    "climate": "Frigid Snowball / Sub-surface Ice",
                    "atmRetention": "Frozen Volatiles Crust",
                    "tidalLock": "Tidally Locked",
                    "uvHazard": "Low",
                    "discoveryMethod": "Transit",
                    "discoveryYear": 2017
                }
            ]
        },
        {
            "id": "kepler-186",
            "title": "Kepler-186 (Host Star + Habitable Zone + Orbits)",
            "starName": "Kepler-186",
            "st_teff": 3788.0,
            "st_radius": 0.472,
            "st_mass": 0.478,
            "spectralType": "M-Dwarf (Red)",
            "starColor": "#ff5252",
            "hzInnerRadius": 0.22,
            "hzOuterRadius": 0.46,
            "nasaEyesUrl": "https://eyes.nasa.gov/apps/exo/#/star/Kepler-186",
            "planets": [
                {
                    "id": "kepler-186-b",
                    "name": "Kepler-186 b",
                    "sma": 0.0378,
                    "ecc": 0.04,
                    "period": 3.88,
                    "radius": 1.07,
                    "mass": 1.24,
                    "temp": 580.0,
                    "insol": 18.5,
                    "esi": 0.340,
                    "score": 0.180,
                    "inHz": False,
                    "status": "CONFIRMED",
                    "color": "#ef4444",
                    "climate": "Scorched Lava Crust",
                    "atmRetention": "Stripped / Thin",
                    "tidalLock": "Tidally Locked",
                    "uvHazard": "High",
                    "discoveryMethod": "Transit",
                    "discoveryYear": 2014
                },
                {
                    "id": "kepler-186-c",
                    "name": "Kepler-186 c",
                    "sma": 0.0573,
                    "ecc": 0.04,
                    "period": 7.27,
                    "radius": 1.25,
                    "mass": 2.10,
                    "temp": 460.0,
                    "insol": 7.8,
                    "esi": 0.480,
                    "score": 0.310,
                    "inHz": False,
                    "status": "CONFIRMED",
                    "color": "#f59e0b",
                    "climate": "Hot Terrestrial (460K)",
                    "atmRetention": "Moderate",
                    "tidalLock": "Tidally Locked",
                    "uvHazard": "High",
                    "discoveryMethod": "Transit",
                    "discoveryYear": 2014
                },
                {
                    "id": "kepler-186-d",
                    "name": "Kepler-186 d",
                    "sma": 0.0864,
                    "ecc": 0.04,
                    "period": 13.34,
                    "radius": 1.40,
                    "mass": 2.70,
                    "temp": 375.0,
                    "insol": 3.2,
                    "esi": 0.610,
                    "score": 0.450,
                    "inHz": False,
                    "status": "CONFIRMED",
                    "color": "#f59e0b",
                    "climate": "Warm Super-Earth",
                    "atmRetention": "Strong",
                    "tidalLock": "Tidally Locked",
                    "uvHazard": "Moderate",
                    "discoveryMethod": "Transit",
                    "discoveryYear": 2014
                },
                {
                    "id": "kepler-186-e",
                    "name": "Kepler-186 e",
                    "sma": 0.1100,
                    "ecc": 0.04,
                    "period": 22.41,
                    "radius": 1.27,
                    "mass": 2.20,
                    "temp": 310.0,
                    "insol": 1.9,
                    "esi": 0.690,
                    "score": 0.580,
                    "inHz": False,
                    "status": "CONFIRMED",
                    "color": "#eab308",
                    "climate": "Warm Temperate Edge",
                    "atmRetention": "Strong",
                    "tidalLock": "Tidally Locked",
                    "uvHazard": "Moderate",
                    "discoveryMethod": "Transit",
                    "discoveryYear": 2014
                },
                {
                    "id": "kepler-186-f",
                    "name": "Kepler-186 f",
                    "sma": 0.4320,
                    "ecc": 0.04,
                    "period": 129.94,
                    "radius": 1.17,
                    "mass": 1.71,
                    "temp": 188.0,
                    "insol": 0.32,
                    "esi": 0.775,
                    "score": 0.775,
                    "inHz": True,
                    "status": "CONFIRMED",
                    "color": "#2ed573",
                    "climate": "Earth-sized / HZ Prime (Liquid Water Capable)",
                    "atmRetention": "Optimal (Atmosphere Retention Capable)",
                    "tidalLock": "Resonant / Unlikely Synchronous",
                    "uvHazard": "Low",
                    "discoveryMethod": "Transit",
                    "discoveryYear": 2014
                }
            ]
        },
        {
            "id": "toi-700",
            "title": "TOI-700 (Host Star + Habitable Zone + Orbits)",
            "starName": "TOI-700",
            "st_teff": 3480.0,
            "st_radius": 0.415,
            "st_mass": 0.416,
            "spectralType": "M-Dwarf (Red)",
            "starColor": "#ff5252",
            "hzInnerRadius": 0.12,
            "hzOuterRadius": 0.25,
            "nasaEyesUrl": "https://eyes.nasa.gov/apps/exo/#/star/TOI-700",
            "planets": [
                {
                    "id": "toi-700-b",
                    "name": "TOI-700 b",
                    "sma": 0.0637,
                    "ecc": 0.03,
                    "period": 9.98,
                    "radius": 1.01,
                    "mass": 1.07,
                    "temp": 440.0,
                    "insol": 5.0,
                    "esi": 0.450,
                    "score": 0.250,
                    "inHz": False,
                    "status": "CONFIRMED",
                    "color": "#ef4444",
                    "climate": "Hot Rocky Terrestrial",
                    "atmRetention": "Thin Atmosphere",
                    "tidalLock": "Tidally Locked",
                    "uvHazard": "Moderate",
                    "discoveryMethod": "TESS Transit",
                    "discoveryYear": 2020
                },
                {
                    "id": "toi-700-c",
                    "name": "TOI-700 c",
                    "sma": 0.0925,
                    "ecc": 0.03,
                    "period": 16.05,
                    "radius": 2.63,
                    "mass": 7.48,
                    "temp": 365.0,
                    "insol": 2.4,
                    "esi": 0.580,
                    "score": 0.420,
                    "inHz": False,
                    "status": "CONFIRMED",
                    "color": "#a1887f",
                    "climate": "Mini-Neptune / Gas Envelope",
                    "atmRetention": "Thick H2/He Envelope",
                    "tidalLock": "Tidally Locked",
                    "uvHazard": "Moderate",
                    "discoveryMethod": "TESS Transit",
                    "discoveryYear": 2020
                },
                {
                    "id": "toi-700-e",
                    "name": "TOI-700 e",
                    "sma": 0.1340,
                    "ecc": 0.03,
                    "period": 27.81,
                    "radius": 0.95,
                    "mass": 0.81,
                    "temp": 273.0,
                    "insol": 1.27,
                    "esi": 0.890,
                    "score": 0.820,
                    "inHz": True,
                    "status": "CONFIRMED",
                    "color": "#2ed573",
                    "climate": "Earth-sized / HZ Inland Ocean",
                    "atmRetention": "Optimal (Water Ocean Likely)",
                    "tidalLock": "Likely Synchronous",
                    "uvHazard": "Low",
                    "discoveryMethod": "TESS Transit",
                    "discoveryYear": 2023
                },
                {
                    "id": "toi-700-d",
                    "name": "TOI-700 d",
                    "sma": 0.1630,
                    "ecc": 0.03,
                    "period": 37.42,
                    "radius": 1.14,
                    "mass": 1.72,
                    "temp": 269.0,
                    "insol": 0.86,
                    "esi": 0.932,
                    "score": 0.890,
                    "inHz": True,
                    "status": "CONFIRMED",
                    "color": "#2ed573",
                    "climate": "Earth-sized / HZ Prime (Temperate)",
                    "atmRetention": "Optimal (Surface Water Capable)",
                    "tidalLock": "Likely Synchronous",
                    "uvHazard": "Low",
                    "discoveryMethod": "TESS Transit",
                    "discoveryYear": 2020
                }
            ]
        },
        {
            "id": "kepler-90",
            "title": "Kepler-90 (8-Planet Solar System Analog)",
            "starName": "Kepler-90",
            "st_teff": 6080.0,
            "st_radius": 1.20,
            "st_mass": 1.20,
            "spectralType": "G-Star (Sun-like Yellow)",
            "starColor": "#ffd32a",
            "hzInnerRadius": 0.98,
            "hzOuterRadius": 1.75,
            "nasaEyesUrl": "https://eyes.nasa.gov/apps/exo/#/star/Kepler-90",
            "planets": [
                { "id": "kepler-90-b", "name": "Kepler-90 b", "sma": 0.074, "ecc": 0.0, "period": 7.0, "radius": 1.31, "mass": 2.3, "temp": 1050.0, "insol": 280.0, "esi": 0.20, "score": 0.05, "inHz": False, "status": "CONFIRMED", "color": "#ef4444", "climate": "Ultra-Hot Terrestrial", "atmRetention": "Stripped", "tidalLock": "Locked", "uvHazard": "Extreme", "discoveryMethod": "Transit", "discoveryYear": 2013 },
                { "id": "kepler-90-c", "name": "Kepler-90 c", "sma": 0.089, "ecc": 0.0, "period": 8.7, "radius": 1.18, "mass": 1.8, "temp": 980.0, "insol": 190.0, "esi": 0.22, "score": 0.08, "inHz": False, "status": "CONFIRMED", "color": "#ef4444", "climate": "Hot Terrestrial", "atmRetention": "Stripped", "tidalLock": "Locked", "uvHazard": "Extreme", "discoveryMethod": "Transit", "discoveryYear": 2013 },
                { "id": "kepler-90-i", "name": "Kepler-90 i", "sma": 0.123, "ecc": 0.0, "period": 14.4, "radius": 1.32, "mass": 2.4, "temp": 709.0, "insol": 60.0, "esi": 0.31, "score": 0.12, "inHz": False, "status": "CONFIRMED", "color": "#f59e0b", "climate": "Hot Super-Earth (AI Discovered)", "atmRetention": "Thin", "tidalLock": "Locked", "uvHazard": "High", "discoveryMethod": "Deep Learning / AI", "discoveryYear": 2017 },
                { "id": "kepler-90-d", "name": "Kepler-90 d", "sma": 0.320, "ecc": 0.0, "period": 59.7, "radius": 2.88, "mass": 9.2, "temp": 518.0, "insol": 16.0, "esi": 0.42, "score": 0.25, "inHz": False, "status": "CONFIRMED", "color": "#a1887f", "climate": "Warm Sub-Neptune", "atmRetention": "Thick Gas Envelope", "tidalLock": "Unlikely Locked", "uvHazard": "Moderate", "discoveryMethod": "Transit", "discoveryYear": 2013 },
                { "id": "kepler-90-e", "name": "Kepler-90 e", "sma": 0.420, "ecc": 0.0, "period": 91.9, "radius": 2.67, "mass": 8.0, "temp": 448.0, "insol": 9.0, "esi": 0.49, "score": 0.32, "inHz": False, "status": "CONFIRMED", "color": "#a1887f", "climate": "Sub-Neptune", "atmRetention": "Thick Envelope", "tidalLock": "Unlikely Locked", "uvHazard": "Moderate", "discoveryMethod": "Transit", "discoveryYear": 2013 },
                { "id": "kepler-90-f", "name": "Kepler-90 f", "sma": 0.480, "ecc": 0.0, "period": 124.9, "radius": 2.89, "mass": 9.3, "temp": 420.0, "insol": 7.0, "esi": 0.52, "score": 0.38, "inHz": False, "status": "CONFIRMED", "color": "#a1887f", "climate": "Sub-Neptune", "atmRetention": "Thick Envelope", "tidalLock": "Unlikely Locked", "uvHazard": "Low", "discoveryMethod": "Transit", "discoveryYear": 2013 },
                { "id": "kepler-90-g", "name": "Kepler-90 g", "sma": 0.710, "ecc": 0.0, "period": 210.6, "radius": 8.13, "mass": 95.0, "temp": 340.0, "insol": 3.0, "esi": 0.58, "score": 0.45, "inHz": False, "status": "CONFIRMED", "color": "#8d6e63", "climate": "Gas Giant (Saturn Analog)", "atmRetention": "Massive Envelope", "tidalLock": "Rapid Rotation", "uvHazard": "Low", "discoveryMethod": "Transit", "discoveryYear": 2013 },
                { "id": "kepler-90-h", "name": "Kepler-90 h", "sma": 1.010, "ecc": 0.0, "period": 331.6, "radius": 11.32, "mass": 318.0, "temp": 292.0, "insol": 1.1, "esi": 0.65, "score": 0.78, "inHz": True, "status": "CONFIRMED", "color": "#2ed573", "climate": "Temperate Jovian Giant (Habitable Moons Capable!)", "atmRetention": "Massive Jovian", "tidalLock": "Rapid Rotation", "uvHazard": "Low", "discoveryMethod": "Transit", "discoveryYear": 2013 }
            ]
        }
    ]
    return {"systems": systems, "total": len(systems)}
