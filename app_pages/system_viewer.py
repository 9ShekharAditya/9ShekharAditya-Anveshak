"""
Page 3: System Viewer — Scientific 3D Planetary System & Habitable Zone Visualizer.

Features:
1. High-Definition 3D Solar System Visualizer:
   - Central Glowing Sun (realistic spectral color and size)
   - Emerald Green Conservative Habitable Zone (Liquid Water Zone)
   - Cyan Optimistic Habitable Zone (Recent Venus to Early Mars)
   - Horizontal Keplerian orbital tracks with planet spheres
   - Interactive Target Planet Reticle
2. Researcher & Astrobiologist Telemetry Deck:
   - Atmospheric Retention Index
   - Jeans Escape Velocity (km/s)
   - UV / Stellar Flaring Hazard Index
   - Equilibrium Temperature vs Greenhouse Offset
   - Earth Similarity Index (ESI) & Composite Habitability Score
3. NASA Eyes on Exoplanets Direct 3D Live Engine
"""

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import numpy as np
import urllib.parse

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from science.orbital import (
    compute_orbit_3d, compute_planet_position,
    generate_hz_disc, generate_sphere
)
from science.habitability import compute_hz_distances
from config import TIER_COLORS


def _get_star_color_and_type(teff):
    """Determine stellar color, glow, and spectral classification."""
    if teff is None or np.isnan(teff):
        return "#ffd32a", "Sun-like (G-type)", "rgba(255, 211, 42, 0.4)"
    if teff < 3500:
        return "#ff3f34", "M-Dwarf (Red)", "rgba(255, 63, 52, 0.4)"
    elif teff < 5000:
        return "#ffa801", "K-Star (Orange)", "rgba(255, 168, 1, 0.4)"
    elif teff < 6000:
        return "#ffd32a", "G-Star (Yellow)", "rgba(255, 211, 42, 0.4)"
    elif teff < 7500:
        return "#f1f2f6", "F-Star (White-Yellow)", "rgba(241, 242, 246, 0.4)"
    else:
        return "#70a1ff", "A/B-Star (Blue-White)", "rgba(112, 161, 255, 0.4)"


def _build_interactive_system_3d(system_planets, host_name, st_teff, st_radius, focused_planet_name=None, time_scrub=0):
    """Build the high-fidelity 3D Plotly planetary system visualization with realistic textured globes, deep space background, and orbital animation."""
    fig = go.Figure()

    # Determine maximum orbital distance for scaling
    smas = [p["semi_major_axis"] for _, p in system_planets.iterrows() if not np.isnan(p.get("semi_major_axis", np.nan))]
    max_sma = max(smas) if smas else 1.0
    bound = max_sma * 1.35

    # 1. HABITABLE ZONE (Discs & Boundaries) 
    hz_outer_display = 0.1
    if st_teff and st_radius and not np.isnan(st_teff) and not np.isnan(st_radius):
        hz = compute_hz_distances(np.array([st_teff]), np.array([st_radius]))
        inner_opt = float(hz["inner_opt"][0])
        inner_con = float(hz["inner_con"][0])
        outer_con = float(hz["outer_con"][0])
        outer_opt = float(hz["outer_opt"][0])
        hz_outer_display = outer_opt
        bound = max(max_sma, hz_outer_display) * 1.35

        # A. Conservative Habitable Zone (Emerald Green - Liquid Water Zone)
        hz_con_disc = generate_hz_disc(inner_con, outer_con)
        fig.add_trace(go.Surface(
            x=hz_con_disc["x"], y=hz_con_disc["y"], z=hz_con_disc["z"],
            colorscale=[[0, "rgba(46, 213, 115, 0.28)"], [1, "rgba(46, 213, 115, 0.28)"]],
            showscale=False,
            name="Conservative Habitable Zone (Liquid Water)",
            hoverinfo="skip",
        ))

        # Conservative Inner Boundary line
        fig.add_trace(go.Scatter3d(
            x=hz_con_disc["inner_x"], y=hz_con_disc["inner_y"], z=np.zeros_like(hz_con_disc["inner_x"]),
            mode="lines",
            line=dict(color="#2ed573", width=4, dash="solid"),
            name="HZ Inner Boundary",
            hovertext=f"Conservative Inner Boundary: {inner_con:.3f} AU",
            hoverinfo="text",
        ))

        # Conservative Outer Boundary line
        fig.add_trace(go.Scatter3d(
            x=hz_con_disc["outer_x"], y=hz_con_disc["outer_y"], z=np.zeros_like(hz_con_disc["outer_x"]),
            mode="lines",
            line=dict(color="#2ed573", width=4, dash="solid"),
            name="HZ Outer Boundary",
            hovertext=f"Conservative Outer Boundary: {outer_con:.3f} AU",
            hoverinfo="text",
        ))

        # B. Optimistic Habitable Zone (Cyan Outer Shell)
        hz_opt_inner_disc = generate_hz_disc(inner_opt, inner_con)
        fig.add_trace(go.Surface(
            x=hz_opt_inner_disc["x"], y=hz_opt_inner_disc["y"], z=hz_opt_inner_disc["z"],
            colorscale=[[0, "rgba(0, 210, 211, 0.1)"], [1, "rgba(0, 210, 211, 0.1)"]],
            showscale=False,
            name="Optimistic Inner Zone",
            hoverinfo="skip",
        ))

        hz_opt_outer_disc = generate_hz_disc(outer_con, outer_opt)
        fig.add_trace(go.Surface(
            x=hz_opt_outer_disc["x"], y=hz_opt_outer_disc["y"], z=hz_opt_outer_disc["z"],
            colorscale=[[0, "rgba(0, 210, 211, 0.1)"], [1, "rgba(0, 210, 211, 0.1)"]],
            showscale=False,
            name="Optimistic Outer Zone",
            hoverinfo="skip",
        ))

        mid_hz = (inner_con + outer_con) / 2
        fig.add_trace(go.Scatter3d(
            x=[0], y=[mid_hz], z=[0],
            mode="text",
            text=["🌿 HABITABLE ZONE (Liquid Water)"],
            textposition="middle center",
            textfont=dict(size=12, color="#2ed573"),
            name="Habitable Zone Marker",
            hoverinfo="skip",
            showlegend=False,
        ))

    # Mesh grid for generating realistic 3D surface spheres (low-poly for fast load)
    n_mesh = 20
    theta_mesh = np.linspace(0, np.pi, n_mesh)
    phi_mesh = np.linspace(0, 2 * np.pi, n_mesh)
    THETA_MESH, PHI_MESH = np.meshgrid(theta_mesh, phi_mesh)

    # Helper function for generating coordinates on a sphere
    def get_sphere_coords(radius, x_center, y_center, z_center):
        xs = radius * np.sin(THETA_MESH) * np.cos(PHI_MESH) + x_center
        ys = radius * np.sin(THETA_MESH) * np.sin(PHI_MESH) + y_center
        zs = radius * np.cos(THETA_MESH) + z_center
        return xs, ys, zs

    #  2. HOST STAR (Glowing 3D Surface Sphere) 
    star_color, star_type, star_glow = _get_star_color_and_type(st_teff)
    star_disp_rad = max(0.025 * bound, min(0.06 * bound, (st_radius or 1.0) * 0.035 * bound))
    
    # Generate solar surface mesh
    sx, sy, sz = get_sphere_coords(star_disp_rad, 0, 0, 0)
    
    # Procedural star flares texture map
    star_texture = np.sin(7 * PHI_MESH) * np.cos(7 * THETA_MESH)

    # Beautiful fiery corona colorscales
    star_colorscales = {
        "M-Dwarf (Red)": [[0, "#4a0e0e"], [0.4, "#b71c1c"], [0.8, "#f44336"], [1, "#ff8a80"]],
        "K-Star (Orange)": [[0, "#5e2900"], [0.4, "#e67e22"], [0.8, "#f39c12"], [1, "#ffeaa7"]],
        "G-Star (Yellow)": [[0, "#5e4a00"], [0.4, "#d4a843"], [0.8, "#f1c40f"], [1, "#ffffff"]],
        "F-Star (White-Yellow)": [[0, "#3d3d4f"], [0.5, "#dcdde1"], [0.8, "#f5f6fa"], [1, "#ffffff"]],
        "A/B-Star (Blue-White)": [[0, "#0c2461"], [0.4, "#4a69bd"], [0.8, "#82ccdd"], [1, "#ffffff"]]
    }
    star_cmap = star_colorscales.get(star_type, [[0, "#5e4a00"], [0.4, "#d4a843"], [0.8, "#f1c40f"], [1, "#ffffff"]])

    # Cool, clean functional hover text
    star_hover = (
        f"<b>⭐ {host_name} ({star_type})</b><br>"
        f"• Spectral Type: {star_type}<br>"
        f"• Temperature: {st_teff:.0f} K<br>"
        f"• Stellar Radius: {st_radius:.2f} R☉<br>"
        f"• System Center: Barycenter (0.00 AU)"
    )

    fig.add_trace(go.Surface(
        x=sx, y=sy, z=sz,
        surfacecolor=star_texture,
        colorscale=star_cmap,
        showscale=False,
        name=f"⭐ Star: {host_name}",
        hovertext=star_hover,
        hoverinfo="text",
    ))

    #  3. PLANETS & ORBIT PATHS 
    palette = ["#5b9bf5", "#ffb74d", "#b388ff", "#3ddc84", "#ff5252", "#00cec9"]

    for i, (_, planet) in enumerate(system_planets.iterrows()):
        sma = planet.get("semi_major_axis")
        if sma is None or np.isnan(sma):
            continue

        ecc = planet.get("eccentricity", 0.0)
        inc = planet.get("inclination", 90.0)
        if ecc is None or np.isnan(ecc):
            ecc = 0.0

        p_name = planet["name"]
        is_focused = (focused_planet_name is not None and p_name == focused_planet_name)
        is_habitable = planet.get("in_hz_conservative", False) or planet.get("in_hz_optimistic", False)
        is_confirmed = planet.get("source") == "Confirmed"
        temp = planet.get("eq_temp", 288.0)
        p_radius = planet.get("radius", 1.0)
        if p_radius is None or np.isnan(p_radius):
            p_radius = 1.0

        base_color = palette[i % len(palette)]
        orbit_color = "#2ed573" if is_habitable else base_color

        # Orbit track
        ox, oy, oz = compute_orbit_3d(sma, ecc, inc, n_points=120)
        fig.add_trace(go.Scatter3d(
            x=ox, y=oy, z=oz,
            mode="lines",
            line=dict(color=orbit_color, width=4 if is_focused else 2.0, dash="solid" if is_habitable else "dot"),
            name=f"Orbit: {p_name}" + (" [IN HZ]" if is_habitable else "") + (" [CONFIRMED]" if is_confirmed else " [CANDIDATE]"),
            hoverinfo="skip",
        ))

        # Position planet on orbit (incorporate time_scrub slider)
        period = planet.get("period", 365.0)
        if period is None or np.isnan(period) or period <= 0:
            period = 365.0
        
        # Calculate angular position shift using the time scrubber
        phase_offset = time_scrub / period
        phase = (i * 0.35 + 0.15 + phase_offset) % 1.0
        px, py, pz = compute_planet_position(sma, ecc, inc, time_fraction=phase)

        # Scale planet radius visually for 3D visibility
        planet_disp_rad = max(0.015 * bound, min(0.04 * bound, p_radius * 0.018 * bound))
        if is_focused:
            planet_disp_rad *= 1.25

        pxs, pys, pzs = get_sphere_coords(planet_disp_rad, px, py, pz)

        # Realistic surface texture generation based on physical properties
        if p_radius > 4.0:
            # Gas Giant bands (wood striped)
            texture = np.sin(10 * THETA_MESH)
            cmap = [[0, "#3e2723"], [0.3, "#8d6e63"], [0.6, "#d7ccc8"], [1.0, "#a1887f"]]
            climate = "Gas Giant (Atmospheric Belts)"
        elif is_habitable:
            # Habitable World Continents (green land, blue sea, white poles)
            texture = np.sin(4 * PHI_MESH) * np.cos(4 * THETA_MESH) + np.cos(1.2 * THETA_MESH) * 0.5
            cmap = [[0, "#0984e3"], [0.35, "#23a6d5"], [0.45, "#2ed573"], [0.8, "#20bf6b"], [1, "#ffffff"]]
            climate = "Temperate (Water Oceans & Landmasses)"
        elif temp > 350:
            # Scorched / Lava cracked planet
            texture = np.sin(10 * PHI_MESH) * np.cos(10 * THETA_MESH)
            cmap = [[0, "#1a0505"], [0.5, "#d35400"], [1.0, "#e74c3c"]]
            climate = "Scorched (Molten Crust)"
        elif temp < 200:
            # Ice sheets / Frozen world
            texture = np.cos(3 * PHI_MESH) * np.sin(3 * THETA_MESH)
            cmap = [[0, "#74b9ff"], [0.5, "#81ecec"], [1.0, "#ffffff"]]
            climate = "Frozen (Glacial Ice Sheets)"
        else:
            # Sandy / Rocky terrain
            texture = np.sin(5 * PHI_MESH) * np.cos(3 * THETA_MESH)
            cmap = [[0, "#574b90"], [0.5, "#ffeaa7"], [1.0, "#f3a683"]]
            climate = "Rocky / Barren Crust"

        status_tag = "✅ Confirmed Planet" if is_confirmed else "🛰️ Candidate"
        planet_hover = (
            f"<b>🪐 {p_name} ({status_tag})</b><br><br>"
            f"• Radius: {p_radius:.2f} R⊕ ({planet.get('size_class', 'Rocky')})<br>"
            f"• Orbit Semimajor Axis: {sma:.4f} AU<br>"
            f"• Period: {period:.1f} days<br>"
            f"• Climate Regime: {climate}<br>"
            f"• Temperature: {temp:.0f} K<br>"
            f"• Earth Similarity (ESI): {planet.get('esi', 0):.2f}"
        )

        fig.add_trace(go.Surface(
            x=pxs, y=pys, z=pzs,
            surfacecolor=texture,
            colorscale=cmap,
            showscale=False,
            name=p_name,
            hovertext=planet_hover,
            hoverinfo="text",
        ))

        # Focus reticle (glowing circle beneath planet)
        if is_focused:
            t_ring = generate_hz_disc(0.015 * bound, 0.02 * bound, n_radial=2, n_theta=30)
            fig.add_trace(go.Scatter3d(
                x=px + t_ring["inner_x"], y=py + t_ring["inner_y"], z=pz + np.zeros_like(t_ring["inner_x"]),
                mode="lines",
                line=dict(color="#ff4757", width=3.5),
                name=f"🎯 Focus: {p_name}",
                hoverinfo="skip",
                showlegend=False,
            ))

    #  4. SCENE BOUNDARIES & CAMERA 
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        images=[
            dict(
                source="https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=2048&auto=format&fit=crop",
                xref="paper", yref="paper",
                x=0, y=1,
                sizex=1, sizey=1,
                sizing="stretch",
                layer="below",
                opacity=0.6
            )
        ],
        scene=dict(
            # Equal ranges and cube aspectmode ensures planets are perfect spheres
            xaxis=dict(range=[-bound * 1.3, bound * 1.3], visible=False, showgrid=False, zeroline=False),
            yaxis=dict(range=[-bound * 1.3, bound * 1.3], visible=False, showgrid=False, zeroline=False),
            zaxis=dict(range=[-bound * 1.3, bound * 1.3], visible=False, showgrid=False, zeroline=False),
            aspectmode='cube',
            camera=dict(eye=dict(x=1.5, y=1.5, z=0.95)),
        ),
        title=dict(
            text=f"🌌 3D System Architecture: {host_name} (Host Star + Habitable Zone + Orbits)",
            font=dict(size=16, color="#d4a843"),
        ),
        height=750,
        margin=dict(l=0, r=0, t=50, b=0),
        legend=dict(
            x=0.01, y=0.99,
            bgcolor="rgba(8,8,16,0.85)",
            bordercolor="rgba(180,155,80,0.25)",
            borderwidth=1,
            font=dict(size=11, color="#8a8070")
        ),
    )

    return fig


def _build_planet_globe(planet_row):
    """Build a 3D sphere globe of the planet colored by predicted thermal climate."""
    temp = planet_row.get("eq_temp", 288.0)
    if temp is None or np.isnan(temp):
        temp = 288.0

    phi = np.linspace(0, 2 * np.pi, 50)
    theta = np.linspace(0, np.pi, 50)
    PHI, THETA = np.meshgrid(phi, theta)

    x = np.sin(THETA) * np.cos(PHI)
    y = np.sin(THETA) * np.sin(PHI)
    z = np.cos(THETA)

    noise = np.sin(5 * PHI) * np.cos(5 * THETA) * 0.08
    r = 1.0 + noise
    x, y, z = r * x, r * y, r * z

    if temp < 200:
        colorscale = "Blues"
        climate = "🧊 Frozen / Ice World (<200K)"
    elif 200 <= temp <= 320:
        colorscale = "Earth"
        climate = "🌍 Temperate / Earth-Analogue (200-320K - Liquid Water Possible!)"
    elif 320 < temp < 500:
        colorscale = "YlOrRd"
        climate = "🌋 Warm / Super-Venus (320-500K)"
    else:
        colorscale = "Hot"
        climate = "🔥 Scorched Lava / Extreme Thermal World (>500K)"

    fig = go.Figure(data=[go.Surface(
        x=x, y=y, z=z,
        surfacecolor=z + noise * 2,
        colorscale=colorscale,
        showscale=False,
        hoverinfo="skip"
    )])

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor="rgba(0,0,0,0)",
            aspectmode="cube"
        ),
        title=f"3D Climate Globe: {planet_row['name']}<br><sub>{climate}</sub>",
        height=380,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


def show(df):
    st.title("3D Planetary System & Habitable Zone Explorer")
    st.caption("High-definition 3D Keplerian orbital mechanics, Kopparapu (2013) Habitable Zones, and researcher astrobiology inferences")

    valid = df[df["semi_major_axis"].notna()].copy()
    if len(valid) == 0:
        st.warning("No planetary systems with orbital distance data available.")
        return

    hosts = valid["host_name"].dropna().unique().tolist()

    #  System Selection 
    st.markdown("### Select Planetary System")
    col1, col2 = st.columns([3, 1])

    with col1:
        search = st.text_input("Search by Star or Planet Name (e.g. Kepler-452, TOI-700, TRAPPIST-1, 10007916)", "")

    with col2:
        category_filter = st.selectbox("Filter systems", [
            "Top Habitable Systems",
            "All Systems (Search)",
            "Multi-Planet Systems",
        ])

    if category_filter == "Top Habitable Systems":
        top = valid.nlargest(40, "habitability_score")
        hosts_filtered = top["host_name"].dropna().unique().tolist()
    elif category_filter == "Multi-Planet Systems":
        counts = valid["host_name"].value_counts()
        multi = counts[counts >= 2].index.tolist()
        hosts_filtered = multi[:50]
    else:
        if search:
            hosts_filtered = [h for h in hosts if search.lower() in str(h).lower()]
            planet_matches = valid[valid["name"].str.lower().str.contains(search.lower(), na=False)]
            hosts_filtered = list(set(hosts_filtered + planet_matches["host_name"].tolist()))
        else:
            hosts_filtered = hosts[:60]

    if not hosts_filtered:
        st.info("No matching systems found. Try a different search term.")
        return

    selected_host = st.selectbox(
        "Choose Star System to Visualize:",
        sorted(hosts_filtered),
        format_func=lambda x: f"{x} ({len(valid[valid['host_name'] == x])} planet{'s' if len(valid[valid['host_name'] == x]) > 1 else ''})"
    )

    system_planets = valid[valid["host_name"] == selected_host]
    if len(system_planets) == 0:
        st.warning("No orbital data available for this system.")
        return

    first = system_planets.iloc[0]
    st_teff = first.get("st_teff")
    st_radius = first.get("st_radius", 1.0)
    planet_names = system_planets["name"].dropna().tolist()

    # Focused Planet Target Selection 
    col_p1, col_p2 = st.columns([2, 2])
    with col_p1:
        focused_planet = st.selectbox(
            "Highlight Planet in 3D Model:",
            ["(None / Show All)"] + planet_names
        )
    with col_p2:
        st.write("Camera View Presets:")
        cam_col1, cam_col2, cam_col3 = st.columns(3)
        with cam_col1:
            cam_3d = st.button("3D Orbit")
        with cam_col2:
            cam_top = st.button("Top-Down (Plane)")
        with cam_col3:
            cam_edge = st.button("Edge-On (Transit)")

    target_planet = None if focused_planet == "(None / Show All)" else focused_planet
    #  3D WebGL Visualizer (Three.js) 
    st.markdown("##### Real-time WebGL Simulation (Drag to Orbit, Scroll to Zoom)")
    from app_pages.threejs_visualizer import render_threejs_system
    render_threejs_system(system_planets, selected_host, st_teff, st_radius, target_planet)

    #  Legend / Explanation Bar 
    st.markdown(
        """
        <div style="background: rgba(20, 20, 50, 0.7); border: 1px solid rgba(100, 100, 255, 0.3); border-radius: 8px; padding: 12px; margin-bottom: 20px;">
            <b>3D Model Legend:</b>
            <span style="color: #ffd32a; margin-left: 15px;">Central Glowing Sun</span>
            <span style="color: #2ed573; margin-left: 15px;">Green Disc = Conservative Habitable Zone (Liquid Water)</span>
            <span style="color: #00d2d3; margin-left: 15px;">Cyan Disc = Optimistic Habitable Zone</span>
            <span style="color: #ff4757; margin-left: 15px;">Red Reticle = Highlighted Planet</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    #  Astrobiologist & Researcher Scientific Inference Deck 
    st.markdown("---")
    st.subheader("Astrobiology & Planetary Science Inferences")
    st.caption("Deep physical modeling for astrobiological assessment and atmospheric characterization feasibility:")

    inspect_p = target_planet if target_planet else planet_names[0]
    p_row = system_planets[system_planets["name"] == inspect_p].iloc[0]

    col_globe, col_telemetry = st.columns([1, 1])

    with col_globe:
        globe_fig = _build_planet_globe(p_row)
        st.plotly_chart(globe_fig, use_container_width=True)

    with col_telemetry:
        st.markdown(f"### Telemetry: **{p_row['name']}**")
        
        if p_row.get("in_hz_conservative"):
            st.success("**Inside Conservative Habitable Zone** (Kopparapu 2013: Runaway to Max Greenhouse)")
        elif p_row.get("in_hz_optimistic"):
            st.info("**Inside Optimistic Habitable Zone** (Recent Venus / Early Mars boundary)")
        else:
            st.warning("**Outside Habitable Zone**")

        st.markdown(f"""
        <div style="background: rgba(20, 25, 60, 0.6); border: 1px solid rgba(100, 150, 255, 0.25); border-radius: 8px; padding: 14px;">
            <b>Planetary Astrophysics & Atmosphere:</b><br>
            • <b>Habitability Composite Score:</b> <span style="color: #2ed573; font-weight: bold;">{p_row.get('habitability_score', 0):.3f}</span> / 1.000<br>
            • <b>Earth Similarity Index (ESI):</b> <span style="color: #2ed573; font-weight: bold;">{p_row.get('esi', 0):.3f}</span> / 1.000<br>
            • <b>AI Confirmation Confidence:</b> <span style="color: #54a0ff; font-weight: bold;">{p_row.get('ai_confidence_pct', 50):.0f}%</span> ({p_row.get('ai_validation_label', 'N/A')})<br>
            • <b>Atmospheric Retention:</b> <span style="color: #70a1ff;">{p_row.get('atm_retention', 'Unknown')}</span> (v_esc = {p_row.get('escape_velocity_kms', 11.2):.1f} km/s)<br>
            • <b>Tidal Lock State:</b> <span style="color: #ffa801;">{p_row.get('tidal_lock', 'Unknown')}</span><br>
            • <b>Stellar UV / Flare Hazard:</b> <span style="color: #ff4757;">{p_row.get('uv_flare_risk', 'Low')}</span><br>
            • <b>Equilibrium Temperature:</b> {p_row.get('eq_temp', 0):.0f} K (Estimated Surface: ~{p_row.get('eq_temp', 0) + 33:.0f} K with 1 bar atmosphere)<br>
            • <b>Orbital Distance & Period:</b> {p_row.get('semi_major_axis', 0):.4f} AU ({p_row.get('period', 0):.1f} days)<br>
            • <b>Radius & Regime:</b> {p_row.get('radius', 1.0):.2f} R⊕ ({p_row.get('size_class', 'Unknown')})
        </div>
        """, unsafe_allow_html=True)

    #  NASA Eyes on Exoplanets — Direct Launch 
    st.markdown("---")
    st.subheader("NASA Eyes on Exoplanets — 3D Universe Explorer")
    st.caption("NASA Eyes blocks iframe embedding for security. Use the buttons below to launch it directly in a new tab:")

    clean_target = str(selected_host).replace(" ", "_")
    eyes_star_url = f"https://eyes.nasa.gov/apps/exo/#/star/{urllib.parse.quote(clean_target)}"
    eyes_home_url = "https://eyes.nasa.gov/apps/exo/"
    archive_url = f"https://exoplanetarchive.ipac.caltech.edu/overview/{urllib.parse.quote(str(selected_host))}"

    # Build a visual launch card with JavaScript window.open for new-tab behavior
    components.html(
        f"""
        <div style="background: linear-gradient(135deg, rgba(10,10,50,0.95), rgba(20,20,80,0.9));
                    border: 2px solid rgba(100, 140, 255, 0.5); border-radius: 14px;
                    padding: 28px; text-align: center; font-family: -apple-system, sans-serif;">
            <h2 style="color: #ffffff; margin: 0 0 6px 0; font-size: 22px;">
                NASA Eyes on Exoplanets
            </h2>
            <p style="color: #a0b4d4; font-size: 14px; margin: 0 0 20px 0;">
                Fly to <b style="color: #54a0ff;">{selected_host}</b> in NASA's official 3D WebGL universe
            </p>
            <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                <a href="{eyes_star_url}" target="_blank" rel="noopener noreferrer"
                   style="background: linear-gradient(135deg, #0984e3, #6c5ce7); color: white;
                          padding: 12px 24px; border-radius: 8px; text-decoration: none;
                          font-weight: bold; font-size: 15px; display: inline-block;
                          transition: transform 0.2s; border: none; cursor: pointer;"
                   onmouseover="this.style.transform='scale(1.05)'"
                   onmouseout="this.style.transform='scale(1.0)'">
                    Fly to {selected_host}
                </a>
                <a href="{eyes_home_url}" target="_blank" rel="noopener noreferrer"
                   style="background: linear-gradient(135deg, #00b894, #00cec9); color: white;
                          padding: 12px 24px; border-radius: 8px; text-decoration: none;
                          font-weight: bold; font-size: 15px; display: inline-block;
                          transition: transform 0.2s; border: none; cursor: pointer;"
                   onmouseover="this.style.transform='scale(1.05)'"
                   onmouseout="this.style.transform='scale(1.0)'">
                    Open Full Universe
                </a>
                <a href="{archive_url}" target="_blank" rel="noopener noreferrer"
                   style="background: linear-gradient(135deg, #636e72, #2d3436); color: white;
                          padding: 12px 24px; border-radius: 8px; text-decoration: none;
                          font-weight: bold; font-size: 15px; display: inline-block;
                          transition: transform 0.2s; border: none; cursor: pointer;"
                   onmouseover="this.style.transform='scale(1.05)'"
                   onmouseout="this.style.transform='scale(1.0)'">
                    NASA Archive Page
                </a>
            </div>
            <p style="color: #636e72; font-size: 11px; margin-top: 16px;">
                Opens in a new browser tab • Requires WebGL-capable browser
            </p>
        </div>
        """,
        height=240,
    )

    #  System Table 
    st.markdown("---")
    st.subheader("📋 System Planetary Telemetry Table")
    display_cols = ["name", "source", "disposition", "radius", "period", "semi_major_axis", "eccentricity",
                    "eq_temp", "esi", "habitability_score", "habitability_tier", "atm_retention", "tidal_lock"]
    available = [c for c in display_cols if c in system_planets.columns]

    st.dataframe(
        system_planets[available].reset_index(drop=True),
        use_container_width=True,
        column_config={
            "name": "Planet",
            "source": "Mission",
            "disposition": "Status",
            "radius": st.column_config.NumberColumn("Radius (R⊕)", format="%.2f"),
            "period": st.column_config.NumberColumn("Period (days)", format="%.2f"),
            "semi_major_axis": st.column_config.NumberColumn("Distance (AU)", format="%.4f"),
            "eccentricity": st.column_config.NumberColumn("Eccentricity", format="%.3f"),
            "eq_temp": st.column_config.NumberColumn("Temp (K)", format="%.0f"),
            "esi": st.column_config.NumberColumn("ESI", format="%.3f"),
            "habitability_score": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=1, format="%.3f"),
            "habitability_tier": "Tier",
            "atm_retention": "Atmosphere Retention",
            "tidal_lock": "Rotation",
        },
    )
