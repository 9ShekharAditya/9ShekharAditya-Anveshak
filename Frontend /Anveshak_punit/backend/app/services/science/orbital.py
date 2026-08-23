"""
science/orbital.py — Generates rich 3D orbital coordinates, 3D star spheres, and Habitable Zone discs.
"""

import numpy as np


def solve_kepler_equation(M, e, tol=1e-8, max_iter=50):
    """Solve Kepler's equation M = E - e*sin(E) using Newton-Raphson."""
    M = np.asarray(M, dtype=float)
    E = M.copy()
    for _ in range(max_iter):
        dE = (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
        E -= dE
        if np.all(np.abs(dE) < tol):
            break
    return E


def compute_orbit_3d(semi_major_axis, eccentricity=0.0, inclination=0.0,
                     omega=0.0, Omega=0.0, n_points=120):
    """
    Generate (x, y, z) coordinates tracing a 3D Keplerian elliptical orbit.
    Default inclination is 0 (horizontal plane) with slight realistic offsets.
    """
    if semi_major_axis is None or np.isnan(semi_major_axis):
        return np.array([0]), np.array([0]), np.array([0])

    a = float(semi_major_axis)
    e = float(eccentricity) if eccentricity is not None and not np.isnan(eccentricity) else 0.0
    e = np.clip(e, 0.0, 0.92)

    # In exoplanet transit catalogs, inclination is given relative to the line of sight (approx 85-90 deg).
    # For a top-down solar system 3D visualization, we map 90 deg transit to the horizontal orbital plane (0 deg tilt):
    raw_inc = float(inclination) if inclination is not None and not np.isnan(inclination) else 90.0
    # Map near-90 transit inclination to small realistic plane tilts (e.g. 0 to 10 deg)
    tilt_deg = abs(90.0 - raw_inc) if abs(90.0 - raw_inc) < 45 else 5.0
    inc_rad = np.radians(tilt_deg)
    
    omega_rad = np.radians(float(omega) if omega is not None and not np.isnan(omega) else 0.0)
    Omega_rad = np.radians(float(Omega) if Omega is not None and not np.isnan(Omega) else 0.0)

    M = np.linspace(0, 2 * np.pi, n_points)
    E = solve_kepler_equation(M, e)

    nu = 2 * np.arctan2(
        np.sqrt(1 + e) * np.sin(E / 2),
        np.sqrt(1 - e) * np.cos(E / 2)
    )
    r = a * (1 - e * np.cos(E))

    x_orb = r * np.cos(nu)
    y_orb = r * np.sin(nu)

    # 3D Euler rotation
    x1 = x_orb * np.cos(omega_rad) - y_orb * np.sin(omega_rad)
    y1 = x_orb * np.sin(omega_rad) + y_orb * np.cos(omega_rad)

    x2 = x1
    y2 = y1 * np.cos(inc_rad)
    z2 = y1 * np.sin(inc_rad)

    x = x2 * np.cos(Omega_rad) - y2 * np.sin(Omega_rad)
    y = x2 * np.sin(Omega_rad) + y2 * np.cos(Omega_rad)
    z = z2

    return x, y, z


def compute_planet_position(semi_major_axis, eccentricity=0.0,
                            inclination=0.0, omega=0.0, Omega=0.0,
                            time_fraction=0.0):
    """Return single (x, y, z) coordinate of a planet along its orbit."""
    a = float(semi_major_axis) if semi_major_axis else 1.0
    e = float(eccentricity) if eccentricity and not np.isnan(eccentricity) else 0.0
    e = np.clip(e, 0.0, 0.92)

    raw_inc = float(inclination) if inclination is not None and not np.isnan(inclination) else 90.0
    tilt_deg = abs(90.0 - raw_inc) if abs(90.0 - raw_inc) < 45 else 5.0
    inc_rad = np.radians(tilt_deg)
    
    omega_rad = np.radians(float(omega) if omega is not None and not np.isnan(omega) else 0.0)
    Omega_rad = np.radians(float(Omega) if Omega is not None and not np.isnan(Omega) else 0.0)

    M = np.array([2 * np.pi * (time_fraction % 1.0)])
    E = solve_kepler_equation(M, e)
    nu = 2 * np.arctan2(
        np.sqrt(1 + e) * np.sin(E / 2),
        np.sqrt(1 - e) * np.cos(E / 2)
    )
    r = a * (1 - e * np.cos(E))

    x_orb = r * np.cos(nu)
    y_orb = r * np.sin(nu)

    x1 = x_orb * np.cos(omega_rad) - y_orb * np.sin(omega_rad)
    y1 = x_orb * np.sin(omega_rad) + y_orb * np.cos(omega_rad)

    x2 = x1
    y2 = y1 * np.cos(inc_rad)
    z2 = y1 * np.sin(inc_rad)

    x = x2 * np.cos(Omega_rad) - y2 * np.sin(Omega_rad)
    y = x2 * np.sin(Omega_rad) + y2 * np.cos(Omega_rad)
    z = z2

    return float(x[0]), float(y[0]), float(z[0])


def generate_hz_disc(inner_au, outer_au, n_radial=15, n_theta=80):
    """Generate high-quality 3D mesh surface for Habitable Zone annular disc."""
    r = np.linspace(inner_au, outer_au, n_radial)
    theta = np.linspace(0, 2 * np.pi, n_theta)
    R, THETA = np.meshgrid(r, theta)

    x = R * np.cos(THETA)
    y = R * np.sin(THETA)
    z = np.zeros_like(x)

    inner_x = inner_au * np.cos(theta)
    inner_y = inner_au * np.sin(theta)
    outer_x = outer_au * np.cos(theta)
    outer_y = outer_au * np.sin(theta)

    return {
        "x": x, "y": y, "z": z,
        "inner_x": inner_x, "inner_y": inner_y,
        "outer_x": outer_x, "outer_y": outer_y,
        "theta": theta,
    }


def generate_sphere(center_x, center_y, center_z, radius, n_points=24):
    """Generate 3D sphere mesh coordinates for stars and planets."""
    phi = np.linspace(0, 2 * np.pi, n_points)
    theta = np.linspace(0, np.pi, n_points)
    PHI, THETA = np.meshgrid(phi, theta)

    x = center_x + radius * np.sin(THETA) * np.cos(PHI)
    y = center_y + radius * np.sin(THETA) * np.sin(PHI)
    z = center_z + radius * np.cos(THETA)

    return x, y, z
