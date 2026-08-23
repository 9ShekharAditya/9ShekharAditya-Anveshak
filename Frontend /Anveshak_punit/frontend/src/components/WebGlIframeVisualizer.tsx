import { useMemo } from 'react';

export default function WebGlIframeVisualizer({ system }: { system: any }) {
  const htmlTemplate = useMemo(() => {
    // Convert React frontend system structure to the JSON structure expected by our ThreeJS script
    const planetsData = system.planets.map((p: any) => ({
      name: p.name,
      sma: p.semiMajorAxisAU || Math.random() * 2,
      ecc: 0,
      period: p.orbitalPeriodDays || 365,
      radius: p.radiusEarth || 1.0,
      temp: p.tempK || 300,
      climate: p.regimeText || 'Unknown',
      color: p.color || '#f3a683',
      is_target: false,
      is_habitable: p.inHz
    }));

    const data = {
      host: {
        name: system.starName || 'Unknown Star',
        teff: 5778, // default as it's not in the TSX system interface directly
        radius: 1.0,
        color: '#ffddaa',
        bound: Math.max(...planetsData.map((p: any) => p.sma)) * 1.5 || 5.0,
        hz_inner: system.hzInnerRadius || 0.5,
        hz_outer: system.hzOuterRadius || 1.5
      },
      planets: planetsData
    };

    const rawHtml = `
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
        <div style="position:absolute; top:-35px; left:50%; transform:translateX(-50%); width:300px; text-align:center; color:#4ade80; font-size:12px; font-weight:bold; background:rgba(0,0,0,0.5); padding:4px 8px; border-radius:4px;">Click a planet to track and zoom in! Click space to reset.</div>
        <label>Orbit Speed</label>
        <input type="range" id="speedSlider" min="0" max="10" step="0.1" value="1">
    </div>
    <div id="three-container" style="width: 100%; height: 100vh;"></div>
    
    <script>
        const data = ${JSON.stringify(data)};
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
                ctx.fillStyle = 'rgba(255, 255, 255, ' + (val/255) + ')';
                ctx.fillRect(i,j,1,1);
            }
        }
        const noiseTex = new THREE.CanvasTexture(canvasTex);
        
        const starMat = new THREE.MeshBasicMaterial({ color: data.host.color, map: noiseTex });
        const star = new THREE.Mesh(starGeom, starMat);
        star.userData = { 
            isStar: true, 
            htmlInfo: "<b style='color:#d4a843;font-size:15px'>⭐ " + data.host.name + "</b><br>Radius: " + data.host.radius.toFixed(2) + " R☉<br>Temperature: " + data.host.teff.toFixed(0) + " K"
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
            
            // Procedural Planet Texture
            const pCanvas = document.createElement('canvas');
            pCanvas.width = 256; pCanvas.height = 256;
            const pCtx = pCanvas.getContext('2d');
            
            // Base color
            pCtx.fillStyle = p.color;
            pCtx.fillRect(0,0,256,256);
            
            // Draw surface noise/bands
            for(let i=0; i<4000; i++) {
                const x = Math.random() * 256;
                const y = Math.random() * 256;
                const w = Math.random() * 15 + 5;
                const h = Math.random() * 4 + 1;
                
                // If it's a gas giant (like jupiter), make bands horizontal
                if (p.climate.includes('Gas') || p.radius > 4.0) {
                    pCtx.fillStyle = 'rgba(255,255,255,0.15)';
                    pCtx.fillRect(x, y, w*4, h*2);
                    pCtx.fillStyle = 'rgba(0,0,0,0.1)';
                    pCtx.fillRect(x, y+2, w*4, h*2);
                } else if (p.climate.includes('Ocean') || p.is_habitable) {
                    // Earth-like clouds & continents
                    pCtx.fillStyle = Math.random() > 0.5 ? 'rgba(255,255,255,0.4)' : 'rgba(34, 139, 34, 0.3)';
                    pCtx.beginPath();
                    pCtx.arc(x, y, w, 0, Math.PI*2);
                    pCtx.fill();
                } else {
                    // Rocky / barren craters
                    pCtx.fillStyle = Math.random() > 0.5 ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.2)';
                    pCtx.beginPath();
                    pCtx.arc(x, y, w/2, 0, Math.PI*2);
                    pCtx.fill();
                }
            }
            const pTex = new THREE.CanvasTexture(pCanvas);
            
            const pMat = new THREE.MeshStandardMaterial({ 
                color: 0xffffff, // we baked the color into the texture
                map: pTex,
                roughness: p.climate.includes('Ocean') ? 0.3 : 0.9, 
                metalness: 0.0 
            });
            const mesh = new THREE.Mesh(pGeom, pMat);
            
            mesh.userData = { 
                isPlanet: true, 
                htmlInfo: "<b style='color:" + p.color + ";font-size:15px'>" + p.name + "</b><br>Radius: " + p.radius.toFixed(2) + " R⊕<br>Orbit: " + p.sma.toFixed(3) + " AU<br>Period: " + p.period.toFixed(1) + " days<br>Temp: " + p.temp.toFixed(0) + " K<br>Climate: " + p.climate 
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

            scene.add(mesh);
            planetMeshes.push({ mesh: mesh, data: p, angle: Math.random() * Math.PI * 2 });
        });

        camera.position.set(0, Math.max(15, data.host.bound * scaleFactor * 0.5), Math.max(25, data.host.bound * scaleFactor * 1.5));
        controls.target.set(0,0,0);

        // Raycaster for Hover Info
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();

        let trackedObject = null;
        window.addEventListener('click', (event) => {
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects(interactables);
            
            if (intersects.length > 0) {
                const obj = intersects[0].object;
                if (obj.userData.isPlanet) {
                    trackedObject = obj;
                } else {
                    trackedObject = null;
                }
            } else {
                trackedObject = null;
            }
        });

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
                const safePeriod = (p.data.period && p.data.period > 0) ? p.data.period : 365;
                const speed = (2.0 / safePeriod) * orbitSpeedMultiplier;
                p.angle += speed; 
                p.mesh.position.x = Math.cos(p.angle) * p.data.sma * scaleFactor;
                p.mesh.position.z = Math.sin(p.angle) * p.data.sma * scaleFactor;
                p.mesh.rotation.y += 0.01 * orbitSpeedMultiplier;
            });

            if (trackedObject) {
                controls.target.copy(trackedObject.position);
            } else {
                controls.target.set(0, 0, 0);
            }
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
    `;
    return rawHtml;
  }, [system]);

  return (
    <iframe
      srcDoc={htmlTemplate}
      style={{ width: '100%', height: '680px', border: 'none', borderRadius: '12px' }}
      title="3D System Visualizer"
    />
  );
}
