import json
import streamlit.components.v1 as components
import numpy as np
from app_pages.system_viewer import _get_star_color_and_type

def render_threejs_system(system_planets, host_name, st_teff, st_radius, target_planet):
    max_sma = system_planets["semi_major_axis"].max()
    bound = float(max_sma) if max_sma and not np.isnan(max_sma) and max_sma > 0 else 1.0
    
    star_color, star_type, _ = _get_star_color_and_type(st_teff)
    
    planets_data = []
    for i, (_, planet) in enumerate(system_planets.iterrows()):
        sma = float(planet.get("semi_major_axis", 1.0) or 1.0)
        ecc = float(planet.get("eccentricity", 0.0) or 0.0)
        period = float(planet.get("period", 365.0) or 365.0)
        p_radius = float(planet.get("radius", 1.0) or 1.0)
        temp = float(planet.get("eq_temp", 288.0) or 288.0)
        is_habitable = bool(planet.get("in_hz_conservative", False) or planet.get("in_hz_optimistic", False))
        
        if p_radius > 4.0: 
            color = "#a1887f"
            climate = "Gas Giant"
        elif is_habitable: 
            color = "#20bf6b"
            climate = "Habitable / Ocean"
        elif temp > 350: 
            color = "#e74c3c"
            climate = "Scorched"
        elif temp < 200: 
            color = "#74b9ff"
            climate = "Frozen"
        else: 
            color = "#f3a683"
            climate = "Rocky"
            
        planets_data.append({
            "name": str(planet.get("name", "Unknown")),
            "sma": sma,
            "ecc": ecc,
            "period": period,
            "radius": p_radius,
            "temp": temp,
            "climate": climate,
            "color": color,
            "is_target": bool(target_planet == planet.get("name")),
            "is_habitable": is_habitable
        })
        
    # Calculate approximate Habitable Zone boundaries
    st_r = float(st_radius) if st_radius and not np.isnan(st_radius) else 1.0
    st_t = float(st_teff) if st_teff and not np.isnan(st_teff) else 5778.0
    luminosity = (st_r ** 2) * ((st_t / 5778.0) ** 4)
    hz_inner = np.sqrt(luminosity / 1.1)
    hz_outer = np.sqrt(luminosity / 0.53)
        
    data = {
        "host": {
            "name": host_name,
            "teff": st_teff,
            "radius": st_r,
            "color": star_color,
            "bound": bound,
            "hz_inner": float(hz_inner),
            "hz_outer": float(hz_outer)
        },
        "planets": planets_data
    }
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body { margin: 0; overflow: hidden; background: #000; color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        #tooltip {
            position: absolute;
            background: rgba(10, 15, 30, 0.9);
            border: 1px solid #d4a843;
            padding: 10px 15px;
            border-radius: 6px;
            color: #fff;
            font-size: 13px;
            pointer-events: none;
            display: none;
            z-index: 100;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            line-height: 1.4;
        }
        #controls {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(20, 25, 40, 0.8);
            padding: 15px 25px;
            border-radius: 30px;
            display: flex;
            align-items: center;
            gap: 15px;
            z-index: 100;
            border: 1px solid rgba(212, 168, 67, 0.4);
        }
        #controls label { font-size: 14px; font-weight: bold; color: #d4a843; }
        input[type=range] { width: 250px; cursor: pointer; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
    <div id="tooltip"></div>
    <div id="controls">
        <label>Orbit Speed</label>
        <input type="range" id="speedSlider" min="0" max="10" step="0.1" value="1">
    </div>
    <div id="three-container" style="width: 100vw; height: 100vh;"></div>
    
    <script>
        const data = __JSON_DATA__;
        const container = document.getElementById('three-container');
        const tooltip = document.getElementById('tooltip');
        const speedSlider = document.getElementById('speedSlider');
        
        let orbitSpeedMultiplier = 1.0;
        speedSlider.addEventListener('input', (e) => {
            orbitSpeedMultiplier = parseFloat(e.target.value);
        });

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x00050a);

        // Procedural Starfield
        const starsGeometry = new THREE.BufferGeometry();
        const starsCount = 4000;
        const posArray = new Float32Array(starsCount * 3);
        const colorArray = new Float32Array(starsCount * 3);
        
        for(let i = 0; i < starsCount * 3; i+=3) {
            const r = 500;
            const theta = 2 * Math.PI * Math.random();
            const phi = Math.acos(2 * Math.random() - 1);
            posArray[i] = r * Math.sin(phi) * Math.cos(theta);
            posArray[i+1] = r * Math.sin(phi) * Math.sin(theta);
            posArray[i+2] = r * Math.cos(phi);

            const starType = Math.random();
            let color = new THREE.Color();
            if (starType > 0.9) color.setHex(0xaaaaee); 
            else if (starType > 0.7) color.setHex(0xeeeedd);
            else color.setHex(0xffffff);
            
            const intensity = 0.4 + Math.random() * 0.6;
            colorArray[i] = color.r * intensity;
            colorArray[i+1] = color.g * intensity;
            colorArray[i+2] = color.b * intensity;
        }
        starsGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
        starsGeometry.setAttribute('color', new THREE.BufferAttribute(colorArray, 3));
        const starsMaterial = new THREE.PointsMaterial({ size: 1.5, vertexColors: true, transparent: true, opacity: 0.9 });
        scene.add(new THREE.Points(starsGeometry, starsMaterial));

        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        container.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;

        const interactables = [];
        const scaleFactor = 15 / Math.max(data.host.bound, 0.1); 

        // Add Star
        const starRadius = Math.max(0.5, Math.min(3.0, data.host.radius));
        const starGeom = new THREE.SphereGeometry(starRadius, 64, 64);
        
        const canvasTex = document.createElement('canvas');
        canvasTex.width = 512; canvasTex.height = 512;
        const ctx = canvasTex.getContext('2d');
        for(let i=0; i<512; i++) {
            for(let j=0; j<512; j++) {
                const val = Math.floor(Math.random() * 60);
                ctx.fillStyle = `rgba(255, 255, 255, ${val/255})`;
                ctx.fillRect(i,j,1,1);
            }
        }
        const noiseTex = new THREE.CanvasTexture(canvasTex);
        
        const starMat = new THREE.MeshBasicMaterial({ color: data.host.color, map: noiseTex });
        const star = new THREE.Mesh(starGeom, starMat);
        star.userData = { 
            isStar: true, 
            htmlInfo: `<b style='color:#d4a843;font-size:15px'>⭐ ${data.host.name}</b><br>Radius: ${data.host.radius.toFixed(2)} R☉<br>Temperature: ${data.host.teff.toFixed(0)} K` 
        };
        scene.add(star);
        interactables.push(star);

        const light = new THREE.PointLight(data.host.color, 2.5, 500);
        scene.add(light);
        scene.add(new THREE.AmbientLight(0x202020));

        // Draw Habitable Zone Disc
        const hzInnerRadius = data.host.hz_inner * scaleFactor;
        const hzOuterRadius = data.host.hz_outer * scaleFactor;
        if (hzInnerRadius > 0 && hzOuterRadius > hzInnerRadius && hzOuterRadius < 300) {
            const hzGeo = new THREE.RingGeometry(hzInnerRadius, hzOuterRadius, 64);
            const hzMat = new THREE.MeshBasicMaterial({ color: 0x2ed573, side: THREE.DoubleSide, transparent: true, opacity: 0.15 });
            const hzMesh = new THREE.Mesh(hzGeo, hzMat);
            hzMesh.rotation.x = Math.PI / 2;
            scene.add(hzMesh);
        }

        // Add Planets
        const planetMeshes = [];
        data.planets.forEach((p) => {
            const dispRadius = Math.max(0.15, Math.min(1.0, p.radius * 0.15));
            const pGeom = new THREE.SphereGeometry(dispRadius, 32, 32);
            const pMat = new THREE.MeshStandardMaterial({ color: p.color, roughness: 0.8, metalness: 0.1 });
            const mesh = new THREE.Mesh(pGeom, pMat);
            
            mesh.userData = { 
                isPlanet: true, 
                htmlInfo: `<b style='color:${p.color};font-size:15px'>🪐 ${p.name}</b><br>Radius: ${p.radius.toFixed(2)} R⊕<br>Orbit: ${p.sma.toFixed(3)} AU<br>Period: ${p.period.toFixed(1)} days<br>Temp: ${p.temp.toFixed(0)} K<br>Climate: ${p.climate}` 
            };
            interactables.push(mesh);
            
            const orbitGeom = new THREE.BufferGeometry();
            const points = [];
            for(let i=0; i<=100; i++) {
                const a = (i/100) * Math.PI * 2;
                points.push(new THREE.Vector3(Math.cos(a)*p.sma*scaleFactor, 0, Math.sin(a)*p.sma*scaleFactor));
            }
            orbitGeom.setFromPoints(points);
            const orbitMat = new THREE.LineBasicMaterial({ color: p.is_habitable ? 0x2ed573 : 0x555555, transparent: true, opacity: 0.5 });
            scene.add(new THREE.Line(orbitGeom, orbitMat));

            if(p.is_target) {
                const ringGeo = new THREE.RingGeometry(dispRadius*1.5, dispRadius*1.8, 32);
                const ringMat = new THREE.MeshBasicMaterial({ color: 0xff4757, side: THREE.DoubleSide });
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.rotation.x = Math.PI / 2;
                mesh.add(ring);
            }

            scene.add(mesh);
            planetMeshes.push({ mesh: mesh, data: p, angle: Math.random() * Math.PI * 2 });
        });

        camera.position.set(0, Math.max(15, data.host.bound * scaleFactor * 0.5), Math.max(25, data.host.bound * scaleFactor * 1.5));
        controls.target.set(0,0,0);

        // Raycaster for Hover Info
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();

        window.addEventListener('mousemove', (event) => {
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
            
            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects(interactables);
            
            if (intersects.length > 0) {
                const obj = intersects[0].object;
                tooltip.innerHTML = obj.userData.htmlInfo;
                tooltip.style.display = 'block';
                tooltip.style.left = (event.clientX + 15) + 'px';
                tooltip.style.top = (event.clientY + 15) + 'px';
                document.body.style.cursor = 'pointer';
            } else {
                tooltip.style.display = 'none';
                document.body.style.cursor = 'default';
            }
        });

        function animate() {
            requestAnimationFrame(animate);
            
            star.rotation.y += 0.001 * orbitSpeedMultiplier;
            
            planetMeshes.forEach(p => {
                // Ensure period is valid to prevent infinity
                const safePeriod = (p.data.period && p.data.period > 0) ? p.data.period : 365;
                const speed = (2.0 / safePeriod) * orbitSpeedMultiplier;
                p.angle += speed; 
                p.mesh.position.x = Math.cos(p.angle) * p.data.sma * scaleFactor;
                p.mesh.position.z = Math.sin(p.angle) * p.data.sma * scaleFactor;
                p.mesh.rotation.y += 0.01 * orbitSpeedMultiplier;
            });

            controls.update();
            renderer.render(scene, camera);
        }
        animate();
        
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
    </script>
    </body>
    </html>
    """
    
    final_html = html_template.replace("__JSON_DATA__", json.dumps(data))
    components.html(final_html, height=750)
