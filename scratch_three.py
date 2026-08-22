import streamlit.components.v1 as components

def get_threejs_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
    <style>body { margin: 0; padding: 0; overflow: hidden; background: #000; }</style>
    </head>
    <body>
    <div id="three-container" style="width: 100vw; height: 100vh;"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script>
        const container = document.getElementById('three-container');
        const scene = new THREE.Scene();
        
        // Starfield background
        const bgTexture = new THREE.TextureLoader().load('https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=2048&auto=format&fit=crop');
        scene.background = bgTexture;

        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 10, 20);

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        container.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;

        // Star
        const starGeometry = new THREE.SphereGeometry(2, 64, 64);
        const starMaterial = new THREE.MeshBasicMaterial({ color: 0xff3300 }); // Red dwarf
        const star = new THREE.Mesh(starGeometry, starMaterial);
        scene.add(star);

        // Planet
        const planetGeo = new THREE.SphereGeometry(0.5, 32, 32);
        const planetMat = new THREE.MeshStandardMaterial({ color: 0x44aa88 });
        const planet = new THREE.Mesh(planetGeo, planetMat);
        scene.add(planet);

        // Light
        const light = new THREE.PointLight(0xffffff, 1.5, 100);
        scene.add(light);
        scene.add(new THREE.AmbientLight(0x404040));

        let time = 0;
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            
            // Orbit planet
            time += 0.01;
            planet.position.x = Math.cos(time) * 10;
            planet.position.z = Math.sin(time) * 10;
            
            renderer.render(scene, camera);
        }
        animate();
    </script>
    </body>
    </html>
    """

print("HTML template ready.")
