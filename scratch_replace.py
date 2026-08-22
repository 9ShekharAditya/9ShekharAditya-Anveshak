import re

with open('app_pages/system_viewer.py', 'r') as f:
    content = f.read()

# We will inject _render_threejs_system before show()
threejs_func = """
import json
import streamlit.components.v1 as components

def _render_threejs_system(system_planets, host_name, st_teff, st_radius, target_planet):
    max_sma = system_planets["semi_major_axis"].max()
    bound = float(max_sma) if max_sma and not __import__("numpy").isnan(max_sma) and max_sma > 0 else 1.0
    
    star_color, star_type, _ = _get_star_color_and_type(st_teff)
    
    planets_data = []
    for i, (_, planet) in enumerate(system_planets.iterrows()):
        sma = float(planet.get("semi_major_axis", 1.0) or 1.0)
        ecc = float(planet.get("eccentricity", 0.0) or 0.0)
        period = float(planet.get("period", 365.0) or 365.0)
        p_radius = float(planet.get("radius", 1.0) or 1.0)
        temp = float(planet.get("eq_temp", 288.0) or 288.0)
        is_habitable = bool(planet.get("in_hz_conservative", False) or planet.get("in_hz_optimistic", False))
        
        if p_radius > 4.0: color = "#a1887f"
        elif is_habitable: color = "#20bf6b"
        elif temp > 350: color = "#e74c3c"
        elif temp < 200: color = "#74b9ff"
        else: color = "#f3a683"
            
        planets_data.append({
            "name": str(planet.get("name", "Unknown")),
            "sma": sma,
            "ecc": ecc,
            "period": period,
            "radius": p_radius,
            "color": color,
            "is_target": bool(target_planet == planet.get("name")),
            "is_habitable": is_habitable
        })
        
    data = {
        "host": {
            "name": host_name,
            "teff": st_teff,
            "radius": float(st_radius) if st_radius and not __import__("numpy").isnan(st_radius) else 1.0,
            "color": star_color,
            "bound": bound
        },
        "planets": planets_data
    }
    
    html_code = f'''
    <!DOCTYPE html>
    <html>
    <head>
    <style>body {{ margin: 0; overflow: hidden; background: #000; color: white; font-family: sans-serif; }}</style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
    <div id="three-container" style="width: 100vw; height: 100vh;"></div>
    <script>
        const data = {json.dumps(data)};
        const container = document.getElementById('three-container');
        const scene = new THREE.Scene();
        
        // Deep space background with milky way
        const textureLoader = new THREE.TextureLoader();
        const bgTexture = textureLoader.load('https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=2048&auto=format&fit=crop');
        scene.background = bgTexture;

        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        
        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        container.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;

        // Add Star
        const starGeom = new THREE.SphereGeometry(data.host.radius * 2, 64, 64);
        
        // Create noise texture for star procedural feel
        const canvas = document.createElement('canvas');
        canvas.width = 256; canvas.height = 256;
        const ctx = canvas.getContext('2d');
        for(let i=0; i<256; i++) {{
            for(let j=0; j<256; j++) {{
                const val = Math.floor(Math.random() * 50);
                ctx.fillStyle = `rgb(${{val}},${{val}},${{val}})`;
                ctx.fillRect(i,j,1,1);
            }}
        }}
        const noiseTex = new THREE.CanvasTexture(canvas);
        
        const starMat = new THREE.MeshBasicMaterial({{ 
            color: data.host.color,
            map: noiseTex
        }});
        const star = new THREE.Mesh(starGeom, starMat);
        scene.add(star);

        // Add Lighting
        const light = new THREE.PointLight(data.host.color, 2.5, 500);
        scene.add(light);
        const ambient = new THREE.AmbientLight(0x202020);
        scene.add(ambient);

        // Add Planets
        const planetMeshes = [];
        const scaleFactor = 10 / data.host.bound; 
        
        data.planets.forEach((p, idx) => {{
            const pGeom = new THREE.SphereGeometry(p.radius * 0.15 + 0.1, 32, 32);
            const pMat = new THREE.MeshStandardMaterial({{ 
                color: p.color,
                roughness: 0.8,
                metalness: 0.1
            }});
            const mesh = new THREE.Mesh(pGeom, pMat);
            
            // Orbit line
            const orbitGeom = new THREE.BufferGeometry();
            const points = [];
            for(let i=0; i<=100; i++) {{
                const a = (i/100) * Math.PI * 2;
                points.push(new THREE.Vector3(Math.cos(a)*p.sma*scaleFactor, 0, Math.sin(a)*p.sma*scaleFactor));
            }}
            orbitGeom.setFromPoints(points);
            const orbitMat = new THREE.LineBasicMaterial({{ 
                color: p.is_habitable ? 0x2ed573 : 0x444444, 
                transparent: true, 
                opacity: 0.5 
            }});
            scene.add(new THREE.Line(orbitGeom, orbitMat));

            scene.add(mesh);
            planetMeshes.push({{ mesh: mesh, data: p, angle: Math.random() * Math.PI * 2 }});
        }});

        camera.position.set(0, 15, 25);
        controls.target.set(0,0,0);

        function animate() {{
            requestAnimationFrame(animate);
            
            star.rotation.y += 0.002;
            
            planetMeshes.forEach(p => {{
                // Speed inversely proportional to period, artificially scaled for web viewing
                p.angle += (1 / (p.data.period || 365)) * 2.0; 
                p.mesh.position.x = Math.cos(p.angle) * p.data.sma * scaleFactor;
                p.mesh.position.z = Math.sin(p.angle) * p.data.sma * scaleFactor;
                p.mesh.rotation.y += 0.01;
            }});

            controls.update();
            renderer.render(scene, camera);
        }}
        animate();
        
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
    </script>
    </body>
    </html>
    '''
    components.html(html_code, height=750)
"""

# Find where show() starts and inject threejs_func before it
import re
new_content = re.sub(r'def show\(', threejs_func + '\ndef show(', content)

# Now, inside show(), replace the plotly chart with the threejs call
# Replace the block:
#     # ── Time / Orbit Scrubber ────────────────────────────────────────
#     ...
#     st.plotly_chart(fig, use_container_width=True)
plot_block_regex = re.compile(r'# ── Time / Orbit Scrubber.*?st\.plotly_chart\(fig, use_container_width=True\)', re.DOTALL)

three_js_call = """# ── 3D Visualizer ────────────────────────────────────────────────
    st.markdown("##### 🚀 Real-time WebGL Simulation (Interact & Orbit)")
    _render_threejs_system(system_planets, selected_host, st_teff, st_radius, target_planet)"""

new_content = plot_block_regex.sub(three_js_call, new_content)

with open('app_pages/system_viewer.py', 'w') as f:
    f.write(new_content)

print("Replaced Plotly with Three.js!")
