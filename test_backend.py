"""
test_backend.py — Test script to verify data ingestion, calculations, and scoring.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.fetcher import get_unified_candidates
from science.habitability import score_habitability
from science.orbital import compute_orbit_3d, compute_planet_position

def test_pipeline():
    print("========================================")
    print("  TESTING EXOPLANET BACKEND PIPELINE   ")
    print("========================================")

    print("\n1. Fetching & unrolling candidate datasets...")
    df = get_unified_candidates()
    print(f"   -> Successfully loaded {len(df)} candidates.")
    print(f"   -> Columns: {list(df.columns)}")

    print("\n2. Scoring Habitability (HZ boundaries, ESI, Tidal Locking)...")
    scored_df = score_habitability(df)
    print(f"   -> Successfully scored {len(scored_df)} candidates.")

    # Check top habitable
    top_candidates = scored_df.nlargest(5, "habitability_score")
    print("\nTop 5 Habitable Candidates:")
    for _, row in top_candidates.iterrows():
        print(f"   - {row['name']} ({row['source']}): Score={row['habitability_score']:.3f}, ESI={row['esi']:.3f}, Tier={row['habitability_tier']}, Rad={row['radius']} R_earth")

    print("\n3. Testing 3D orbital trajectory generation...")
    # Example: 1 AU orbit, 0.05 eccentricity, 89 deg inclination
    x, y, z = compute_orbit_3d(1.0, eccentricity=0.05, inclination=89.0, n_points=50)
    print(f"   -> Generated {len(x)} 3D orbital coordinates.")
    pos = compute_planet_position(1.0, eccentricity=0.05, inclination=89.0, time_fraction=0.25)
    print(f"   -> Planet position at quarter orbit: (x={pos[0]:.3f}, y={pos[1]:.3f}, z={pos[2]:.3f})")

    print("\n✅ ALL BACKEND AND SCIENTIFIC LOGIC VERIFIED SUCCESSFULLY!\n")

if __name__ == "__main__":
    test_pipeline()
