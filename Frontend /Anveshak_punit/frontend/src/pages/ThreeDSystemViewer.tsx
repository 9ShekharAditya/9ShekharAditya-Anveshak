import React, { useState, useRef, useEffect, useMemo } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import {
  Orbit, Eye, Globe2, Award, ExternalLink, Play, Pause, RotateCcw
} from 'lucide-react';

/* ─── Types ──────────────────────────────────────────────── */

interface CandidateRaw {
  id: string;
  name: string;
  system: string;
  radius: number;
  mass: number;
  orbitalDistance: number;
  orbitalPeriod: number;
  equilibriumTemp: number;
  stellarTemp: number;
  stellarRadius: number;
  hzInnerCon?: number;
  hzOuterCon?: number;
  hzInnerOpt?: number;
  hzOuterOpt?: number;
  inHz: boolean;
  score: number;
  habitabilityClass: string;
  discoveryMethod: string;
  discoveryYear: number;
  mission: string;
  temp: number;
  period: number;
  insol: number;
  esi: number;
  sizeClass: string;
  tidalLock: string;
}

interface PlanetModel {
  id: string;
  name: string;
  sma: number;
  ecc: number;
  period: number;
  radius: number;
  temp: number;
  insol: number;
  esi: number;
  score: number;
  inHz: boolean;
  status: string;
  color: string;
  climate: string;
  atmRetention: string;
  tidalLock: string;
  uvHazard: string;
  discoveryMethod: string;
  discoveryYear: number;
}

interface SystemModel {
  id: string;
  name: string;
  st_teff: number;
  st_radius: number;
  starColor: string;
  starType: string;
  hzInner: number;
  hzOuter: number;
  planets: PlanetModel[];
}

/* ─── Helpers & Realistic Procedural Planet Textures ─────── */

function getStarProps(teff: number): { color: string; type: string } {
  if (!teff || isNaN(teff)) return { color: '#ffd32a', type: 'Sun-like (G-type)' };
  if (teff < 3500) return { color: '#ff4d4d', type: 'M-Dwarf (Red)' };
  if (teff < 5000) return { color: '#ffa801', type: 'K-Star (Orange)' };
  if (teff < 6000) return { color: '#ffd32a', type: 'G-Star (Yellow Sun)' };
  if (teff < 7500) return { color: '#f1f2f6', type: 'F-Star (White-Yellow)' };
  return { color: '#70a1ff', type: 'A/B-Star (Blue-White)' };
}

function getPlanetClimate(radius: number, temp: number, inHz: boolean): { color: string; climate: string } {
  if (radius > 4.0) {
    return { color: '#d7a15c', climate: 'Gas Giant (Jovian / Saturnian)' };
  }
  if (inHz || (temp >= 200 && temp <= 320)) {
    return { color: '#2ed573', climate: 'Temperate / Liquid Oceans & Continents' };
  }
  if (temp > 350) {
    return { color: '#ff4757', climate: 'Scorched / Lava & Molten Basalt' };
  }
  if (temp < 200) {
    return { color: '#70a1ff', climate: 'Frozen / Ice & Glacial Plains' };
  }
  return { color: '#e67e22', climate: 'Rocky / Desert & Terracotta Dunes' };
}

/**
 * Creates high-detail procedural 2D canvas texture map for realistic 3D planets
 */
function createPlanetTexture(planet: PlanetModel): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 256;
  const ctx = canvas.getContext('2d')!;

  const { radius, temp, inHz, climate } = planet;

  if (radius > 4.0 || climate.includes('Jovian') || climate.includes('Gas Giant')) {
    // ── Gas Giant / Jovian Planetary Bands ──
    const grad = ctx.createLinearGradient(0, 0, 0, 256);
    grad.addColorStop(0.0, '#a06e3b');
    grad.addColorStop(0.12, '#eed9c4');
    grad.addColorStop(0.24, '#c89d7c');
    grad.addColorStop(0.38, '#7e481f');
    grad.addColorStop(0.50, '#f4ece1');
    grad.addColorStop(0.64, '#b07d4b');
    grad.addColorStop(0.78, '#5d3113');
    grad.addColorStop(0.90, '#d1a87e');
    grad.addColorStop(1.0, '#864f24');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 512, 256);

    // Fine zonal atmospheric turbulence
    for (let y = 0; y < 256; y += 3) {
      const alpha = 0.12 + Math.sin(y * 0.15) * 0.08;
      ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
      ctx.fillRect(0, y, 512, 1.5);
    }
    // Great Jovian Storm Oval
    ctx.fillStyle = '#b71c1c';
    ctx.beginPath();
    ctx.ellipse(320, 150, 42, 22, 0.08, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#ef5350';
    ctx.lineWidth = 3;
    ctx.stroke();
  } else if (inHz || (temp >= 200 && temp <= 320)) {
    // ── Habitable / Earth-like Ocean World ──
    // Deep Sapphire Blue Ocean
    ctx.fillStyle = '#00529b';
    ctx.fillRect(0, 0, 512, 256);

    // Emerald Continents & Landmasses
    for (let c = 0; c < 14; c++) {
      const cx = (c * 39 + 15) % 512;
      const cy = 55 + ((c * 31) % 145);
      const cr = 28 + (c % 5) * 10;
      
      // Coastal shallows
      ctx.fillStyle = '#26c6da';
      ctx.beginPath();
      ctx.arc(cx, cy, cr * 1.18, 0, Math.PI * 2);
      ctx.fill();

      // Lush forest land
      ctx.fillStyle = '#2e7d32';
      ctx.beginPath();
      ctx.arc(cx, cy, cr, 0, Math.PI * 2);
      ctx.fill();

      // Mountain / Highland plateaus
      ctx.fillStyle = '#8d6e63';
      ctx.beginPath();
      ctx.arc(cx + 4, cy + 3, cr * 0.5, 0, Math.PI * 2);
      ctx.fill();
    }

    // Polar Ice Caps
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 512, 24);
    ctx.fillRect(0, 232, 512, 24);

    // Swirling Dynamic Clouds
    for (let i = 0; i < 22; i++) {
      const x = (i * 26 + Math.sin(i * 1.5) * 40) % 512;
      const y = 30 + ((i * 18) % 196);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.65)';
      ctx.beginPath();
      ctx.ellipse(x, y, 50, 14, 0.15, 0, Math.PI * 2);
      ctx.fill();
    }
  } else if (temp > 350) {
    // ── Scorched / Lava World ──
    ctx.fillStyle = '#1c1917'; // Basalt crust
    ctx.fillRect(0, 0, 512, 256);

    // Glowing Lava Fissures & Calderas
    ctx.strokeStyle = '#ff3838';
    ctx.lineWidth = 4;
    ctx.shadowColor = '#ff9f1a';
    ctx.shadowBlur = 12;
    for (let i = 0; i < 20; i++) {
      const x = (i * 29) % 512;
      const y = (i * 19) % 256;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo((x + 45) % 512, y + 25);
      ctx.lineTo((x + 85) % 512, y + 10);
      ctx.stroke();
    }
    ctx.shadowBlur = 0;
  } else if (temp < 200) {
    // ── Frozen / Ice World ──
    const grad = ctx.createLinearGradient(0, 0, 0, 256);
    grad.addColorStop(0.0, '#ffffff');
    grad.addColorStop(0.2, '#b3e5fc');
    grad.addColorStop(0.5, '#4fc3f7');
    grad.addColorStop(0.8, '#81d4fa');
    grad.addColorStop(1.0, '#ffffff');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 512, 256);

    // Deep cyan glacial fissures
    ctx.strokeStyle = '#0288d1';
    ctx.lineWidth = 2.5;
    for (let i = 0; i < 18; i++) {
      const x = (i * 33) % 512;
      const y = (i * 21) % 256;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo((x + 55) % 512, y + 35);
      ctx.stroke();
    }
  } else {
    // ── Rocky / Desert Mars-like ──
    const grad = ctx.createLinearGradient(0, 0, 0, 256);
    grad.addColorStop(0, '#c0392b');
    grad.addColorStop(0.5, '#d35400');
    grad.addColorStop(1, '#a04000');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 512, 256);

    // Craters & Dunes
    for (let i = 0; i < 30; i++) {
      const cx = (i * 21) % 512;
      const cy = (i * 15) % 256;
      ctx.fillStyle = '#6e2c00';
      ctx.beginPath();
      ctx.arc(cx, cy, 7 + (i % 8), 0, Math.PI * 2);
      ctx.fill();
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  return texture;
}

/* ─── 3D Climate Globe Component ─────────────────────────── */

function AnimatedClimateGlobe({ planet }: { planet: PlanetModel }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let rotation = 0;

    const renderGlobe = () => {
      rotation += 0.012;
      const w = canvas.width;
      const h = canvas.height;
      const cx = w / 2;
      const cy = h / 2;
      const R = Math.min(w, h) * 0.42;

      ctx.clearRect(0, 0, w, h);

      // Temperature outer aura
      const isWarm = planet.temp > 320;
      const atmosGlow = ctx.createRadialGradient(cx, cy, R * 0.9, cx, cy, R * 1.35);
      atmosGlow.addColorStop(0, planet.inHz ? 'rgba(46, 213, 115, 0.4)' : isWarm ? 'rgba(239, 68, 68, 0.3)' : 'rgba(116, 185, 255, 0.3)');
      atmosGlow.addColorStop(0.5, planet.inHz ? 'rgba(46, 213, 115, 0.1)' : isWarm ? 'rgba(239, 68, 68, 0.06)' : 'rgba(116, 185, 255, 0.06)');
      atmosGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = atmosGlow;
      ctx.beginPath();
      ctx.arc(cx, cy, R * 1.35, 0, Math.PI * 2);
      ctx.fill();

      // Planet Sphere
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, R, 0, Math.PI * 2);
      ctx.clip();

      const baseGrad = ctx.createRadialGradient(cx - R * 0.3, cy - R * 0.3, 0, cx, cy, R);
      baseGrad.addColorStop(0, planet.color);
      baseGrad.addColorStop(1, '#05070d');
      ctx.fillStyle = baseGrad;
      ctx.fill();

      // Atmospheric Bands & Surface Continents
      for (let b = -3; b <= 3; b++) {
        const bandY = cy + b * (R * 0.25);
        const bandR = Math.sqrt(Math.max(0, R * R - Math.pow(b * (R * 0.25), 2)));
        const shift = Math.sin(rotation + b * 0.8) * (R * 0.15);
        ctx.strokeStyle = planet.inHz ? 'rgba(255, 255, 255, 0.35)' : 'rgba(255, 255, 255, 0.18)';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.ellipse(cx + shift, bandY, bandR * 0.95, bandR * 0.2, 0, 0, Math.PI * 2);
        ctx.stroke();
      }

      ctx.restore();

      // Specular 3D Highlight
      const specGrad = ctx.createRadialGradient(cx - R * 0.35, cy - R * 0.35, 0, cx - R * 0.35, cy - R * 0.35, R * 0.5);
      specGrad.addColorStop(0, 'rgba(255, 255, 255, 0.45)');
      specGrad.addColorStop(0.5, 'rgba(255, 255, 255, 0.08)');
      specGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
      ctx.fillStyle = specGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, R, 0, Math.PI * 2);
      ctx.fill();

      animId = requestAnimationFrame(renderGlobe);
    };

    renderGlobe();
    return () => cancelAnimationFrame(animId);
  }, [planet]);

  return (
    <div className="relative flex items-center justify-center w-full h-[240px]">
      <canvas ref={canvasRef} width={260} height={260} className="block" />
    </div>
  );
}

/* ─── Main 3D System Viewer ──────────────────────────────── */

export default function ThreeDSystemViewer() {
  const [candidates, setCandidates] = useState<CandidateRaw[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Search & Filtering Controls
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('Top Habitable Systems');
  const [selectedHostName, setSelectedHostName] = useState<string>('TRAPPIST-1');
  const [highlightPlanetName, setHighlightPlanetName] = useState<string>('(None / Show All)');
  const [activeTelemetryPlanetName, setActiveTelemetryPlanetName] = useState<string>('');

  // Simulation Controls
  const [orbitSpeed, setOrbitSpeed] = useState<number>(1.0);
  const [isPaused, setIsPaused] = useState<boolean>(false);

  // Hover Tooltip
  const [hoveredPlanet, setHoveredPlanet] = useState<PlanetModel | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);

  // Fetch full 16,000+ candidates catalog
  useEffect(() => {
    fetch('/api/v1/science/candidates')
      .then((res) => res.json())
      .then((data) => {
        if (data && Array.isArray(data.candidates)) {
          setCandidates(data.candidates);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        console.error('Error fetching exoplanet data:', err);
        setIsLoading(false);
      });
  }, []);

  // Group all candidates by host system
  const systemMap = useMemo(() => {
    const map = new Map<string, CandidateRaw[]>();
    for (const c of candidates) {
      const host = c.system || 'Unknown Host';
      if (!map.has(host)) {
        map.set(host, []);
      }
      map.get(host)!.push(c);
    }
    return map;
  }, [candidates]);

  // Filter systems list based on category & search term
  const filteredHostNames = useMemo(() => {
    const allHosts = Array.from(systemMap.keys());
    let filtered = allHosts;

    if (categoryFilter === 'Top Habitable Systems') {
      const topHosts = new Set<string>();
      const sortedCandidates = [...candidates].sort((a, b) => (b.score || 0) - (a.score || 0));
      for (const c of sortedCandidates) {
        if (c.system && !topHosts.has(c.system)) {
          topHosts.add(c.system);
          if (topHosts.size >= 60) break;
        }
      }
      filtered = Array.from(topHosts);
    } else if (categoryFilter === 'Multi-Planet Systems') {
      filtered = allHosts.filter((host) => {
        const list = systemMap.get(host);
        return list && list.length >= 2;
      }).sort((a, b) => (systemMap.get(b)?.length || 0) - (systemMap.get(a)?.length || 0));
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      filtered = allHosts.filter((host) => {
        if (host.toLowerCase().includes(q)) return true;
        const planets = systemMap.get(host) || [];
        return planets.some((p) => p.name.toLowerCase().includes(q));
      });
    }

    return filtered;
  }, [systemMap, categoryFilter, searchQuery, candidates]);

  // Construct active system model
  const activeSystem = useMemo<SystemModel>(() => {
    const rawList = systemMap.get(selectedHostName) || systemMap.get('TRAPPIST-1') || [];
    const first = rawList[0] || ({} as CandidateRaw);

    const st_teff = first.stellarTemp || 5778;
    const st_radius = first.stellarRadius || 1.0;
    const { color: starColor, type: starType } = getStarProps(st_teff);

    // Habitable zone calculation: use accurate Kopparapu distances from physics engine
    const luminosity = Math.pow(st_radius, 2) * Math.pow(st_teff / 5778, 4);
    const hzInner = first.hzInnerCon && first.hzInnerCon > 0
      ? first.hzInnerCon
      : Math.max(0.01, Math.sqrt(luminosity / 1.1));
    const hzOuter = first.hzOuterCon && first.hzOuterCon > 0
      ? first.hzOuterCon
      : Math.max(0.03, Math.sqrt(luminosity / 0.53));

    const planets: PlanetModel[] = rawList.map((p) => {
      const sma = p.orbitalDistance > 0 ? p.orbitalDistance : Math.pow((p.period || 365.25) / 365.25, 2 / 3);
      const { color, climate } = getPlanetClimate(p.radius || 1.0, p.equilibriumTemp || 288, p.inHz);
      const isConfirmed = p.mission === 'Confirmed';

      return {
        id: p.id || p.name,
        name: p.name,
        sma: Math.max(0.005, sma),
        ecc: 0.0,
        period: p.period > 0 ? p.period : 365.25,
        radius: p.radius > 0 ? p.radius : 1.0,
        temp: p.equilibriumTemp || 288,
        insol: p.insol || 1.0,
        esi: p.esi || 0.0,
        score: p.score || 0.0,
        inHz: Boolean(p.inHz),
        status: isConfirmed ? 'CONFIRMED' : 'CANDIDATE',
        color,
        climate,
        atmRetention: p.radius < 1.6 ? 'Atmosphere Retention Feasible' : 'Thick Volatile Envelope',
        tidalLock: sma < 0.1 ? 'Likely Tidally Locked' : 'Unlikely Locked (Diurnal Cycle Active)',
        uvHazard: st_teff < 3800 ? 'Moderate (M-Dwarf Stellar Activity)' : 'Low (Quiet Host Star)',
        discoveryMethod: p.discoveryMethod || p.mission || 'Transit',
        discoveryYear: p.discoveryYear || 2020,
      };
    }).sort((a, b) => a.sma - b.sma);

    return {
      id: selectedHostName.toLowerCase().replace(/\s+/g, '-'),
      name: selectedHostName,
      st_teff,
      st_radius,
      starColor,
      starType,
      hzInner,
      hzOuter,
      planets,
    };
  }, [selectedHostName, systemMap]);

  // Selected planet for telemetry deck
  const activeTelemetryPlanet = useMemo(() => {
    if (!activeSystem.planets.length) return null;
    if (activeTelemetryPlanetName) {
      const found = activeSystem.planets.find((p) => p.name === activeTelemetryPlanetName);
      if (found) return found;
    }
    return activeSystem.planets[0];
  }, [activeSystem, activeTelemetryPlanetName]);

  // ── Three.js WebGL Real-time 3D Simulation ─────────────────────
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }

    const width = container.clientWidth || 800;
    const height = Math.max(580, container.clientHeight || 580);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x00050a);

    // 1. Procedural 3D Starfield
    const starsGeometry = new THREE.BufferGeometry();
    const starsCount = 4000;
    const posArray = new Float32Array(starsCount * 3);
    const colorArray = new Float32Array(starsCount * 3);

    for (let i = 0; i < starsCount * 3; i += 3) {
      const r = 480;
      const theta = 2 * Math.PI * Math.random();
      const phi = Math.acos(2 * Math.random() - 1);
      posArray[i] = r * Math.sin(phi) * Math.cos(theta);
      posArray[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      posArray[i + 2] = r * Math.cos(phi);

      const starType = Math.random();
      const color = new THREE.Color();
      if (starType > 0.88) color.setHex(0xaaaaee);
      else if (starType > 0.68) color.setHex(0xeeeedd);
      else color.setHex(0xffffff);

      const intensity = 0.35 + Math.random() * 0.65;
      colorArray[i] = color.r * intensity;
      colorArray[i + 1] = color.g * intensity;
      colorArray[i + 2] = color.b * intensity;
    }

    starsGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    starsGeometry.setAttribute('color', new THREE.BufferAttribute(colorArray, 3));
    const starsMaterial = new THREE.PointsMaterial({ size: 1.4, vertexColors: true, transparent: true, opacity: 0.85 });
    scene.add(new THREE.Points(starsGeometry, starsMaterial));

    // 2. Camera & WebGL Renderer
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1500);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.maxDistance = 400;
    controls.minDistance = 2;
    controlsRef.current = controls;

    // Scale Factor calculation for solar system bounds
    const maxSma = Math.max(...activeSystem.planets.map((p) => p.sma || 0.1), activeSystem.hzOuter, 0.1);
    const minSma = Math.min(...activeSystem.planets.map((p) => p.sma || 0.1), activeSystem.hzInner, 0.1);
    const scaleFactor = 28 / maxSma;

    // Proportional Star Radius (Ensures innermost planet orbit is never swallowed)
    const minOrbitRadius = minSma * scaleFactor;
    const starRadius = Math.max(0.5, Math.min(minOrbitRadius * 0.45, (activeSystem.st_radius || 1.0) * 1.5, 2.4));
    const starGeom = new THREE.SphereGeometry(starRadius, 64, 64);

    const starCanvas = document.createElement('canvas');
    starCanvas.width = 512;
    starCanvas.height = 512;
    const sCtx = starCanvas.getContext('2d')!;
    for (let i = 0; i < 512; i++) {
      for (let j = 0; j < 512; j++) {
        const val = Math.floor(Math.random() * 65);
        sCtx.fillStyle = `rgba(255, 255, 255, ${val / 255})`;
        sCtx.fillRect(i, j, 1, 1);
      }
    }
    const noiseTex = new THREE.CanvasTexture(starCanvas);
    const starMat = new THREE.MeshBasicMaterial({ color: activeSystem.starColor, map: noiseTex });
    const starMesh = new THREE.Mesh(starGeom, starMat);
    scene.add(starMesh);

    // Glowing Sun Atmosphere Corona
    const coronaGeo = new THREE.SphereGeometry(starRadius * 1.25, 32, 32);
    const coronaMat = new THREE.MeshBasicMaterial({
      color: activeSystem.starColor,
      transparent: true,
      opacity: 0.28,
      side: THREE.BackSide,
    });
    scene.add(new THREE.Mesh(coronaGeo, coronaMat));

    // ── Bright Lighting Setup (Ensures planets are vivid and never dark!) ──
    const starLight = new THREE.PointLight(activeSystem.starColor, 4.5, 600);
    scene.add(starLight);

    // Comprehensive ambient fill so both sides of planet textures are clearly illuminated
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.4);
    scene.add(ambientLight);

    // Directional light from above to give realistic 3D depth and specular reflections
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(30, 60, 30);
    scene.add(dirLight);

    // 4. Habitable Zone Ring Disc (Emerald Green)
    const hzIn = activeSystem.hzInner * scaleFactor;
    const hzOut = activeSystem.hzOuter * scaleFactor;

    if (hzIn > 0 && hzOut > hzIn && hzOut < 350) {
      const hzGeo = new THREE.RingGeometry(hzIn, hzOut, 96);
      const hzMat = new THREE.MeshBasicMaterial({
        color: 0x2ed573,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.16,
      });
      const hzMesh = new THREE.Mesh(hzGeo, hzMat);
      hzMesh.rotation.x = Math.PI / 2;
      scene.add(hzMesh);

      // Inner boundary line
      const inLineGeo = new THREE.BufferGeometry();
      const inPts: THREE.Vector3[] = [];
      for (let i = 0; i <= 100; i++) {
        const a = (i / 100) * Math.PI * 2;
        inPts.push(new THREE.Vector3(Math.cos(a) * hzIn, 0, Math.sin(a) * hzIn));
      }
      inLineGeo.setFromPoints(inPts);
      scene.add(new THREE.Line(inLineGeo, new THREE.LineBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.6 })));

      // Outer boundary line
      const outLineGeo = new THREE.BufferGeometry();
      const outPts: THREE.Vector3[] = [];
      for (let i = 0; i <= 100; i++) {
        const a = (i / 100) * Math.PI * 2;
        outPts.push(new THREE.Vector3(Math.cos(a) * hzOut, 0, Math.sin(a) * hzOut));
      }
      outLineGeo.setFromPoints(outPts);
      scene.add(new THREE.Line(outLineGeo, new THREE.LineBasicMaterial({ color: 0x34d399, transparent: true, opacity: 0.6 })));
    }

    // 5. Planetary Orbits & Real Textured 3D Planet Spheres
    const planetMeshes: Array<{
      mesh: THREE.Mesh;
      planet: PlanetModel;
      angle: number;
      orbitRadius: number;
      speed: number;
    }> = [];

    const interactableObjects: THREE.Object3D[] = [];

    activeSystem.planets.forEach((p, idx) => {
      const orbitR = p.sma * scaleFactor;

      // Circular Keplerian Orbit Path
      const orbitGeom = new THREE.BufferGeometry();
      const pts: THREE.Vector3[] = [];
      for (let i = 0; i <= 120; i++) {
        const a = (i / 120) * Math.PI * 2;
        pts.push(new THREE.Vector3(Math.cos(a) * orbitR, 0, Math.sin(a) * orbitR));
      }
      orbitGeom.setFromPoints(pts);
      const orbitLine = new THREE.Line(
        orbitGeom,
        new THREE.LineBasicMaterial({
          color: p.inHz ? 0x2ed573 : 0x64748b,
          transparent: true,
          opacity: p.inHz ? 0.75 : 0.45,
        })
      );
      scene.add(orbitLine);

      // Realistic 3D Planet Sphere with Procedural Surface Map & Atmosphere
      const dispRadius = Math.max(0.42, Math.min(1.7, p.radius * 0.35));
      const pGeom = new THREE.SphereGeometry(dispRadius, 48, 48);

      const pTex = createPlanetTexture(p);
      const pMat = new THREE.MeshStandardMaterial({
        map: pTex,
        roughness: 0.4,
        metalness: 0.05,
        emissive: new THREE.Color(p.color),
        emissiveIntensity: 0.22,
        emissiveMap: pTex,
      });
      const pMesh = new THREE.Mesh(pGeom, pMat);
      pMesh.userData = { planet: p };

      // Add a subtle glowing atmospheric halo for Earth-like / Habitable planets
      if (p.inHz || (p.temp >= 200 && p.temp <= 320)) {
        const atmosHaloGeo = new THREE.SphereGeometry(dispRadius * 1.14, 32, 32);
        const atmosHaloMat = new THREE.MeshBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.32,
          side: THREE.BackSide,
        });
        pMesh.add(new THREE.Mesh(atmosHaloGeo, atmosHaloMat));
      }

      scene.add(pMesh);
      interactableObjects.push(pMesh);

      // Focus Reticle Ring if highlighted
      const isTarget = highlightPlanetName === p.name;
      if (isTarget) {
        const rGeo = new THREE.RingGeometry(dispRadius * 1.6, dispRadius * 2.0, 32);
        const rMat = new THREE.MeshBasicMaterial({ color: 0xff4757, side: THREE.DoubleSide });
        const reticle = new THREE.Mesh(rGeo, rMat);
        reticle.rotation.x = Math.PI / 2;
        pMesh.add(reticle);
      }

      const initialAngle = (idx / activeSystem.planets.length) * Math.PI * 2 + 0.2;
      const safePeriod = p.period > 0 ? p.period : 365.25;
      const angularSpeed = 2.0 / safePeriod;

      planetMeshes.push({
        mesh: pMesh,
        planet: p,
        angle: initialAngle,
        orbitRadius: orbitR,
        speed: angularSpeed,
      });
    });

    // Default Camera View: 3D Orbit isometric
    camera.position.set(0, Math.max(16, maxSma * scaleFactor * 0.6), Math.max(26, maxSma * scaleFactor * 1.3));
    controls.target.set(0, 0, 0);

    // 6. Interactive Mouse Raycasting & Hover
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const onMouseMove = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(interactableObjects);

      if (intersects.length > 0) {
        const hitPlanet = intersects[0].object.userData.planet as PlanetModel;
        setHoveredPlanet(hitPlanet);
        setTooltipPos({ x: event.clientX - rect.left, y: event.clientY - rect.top });
        renderer.domElement.style.cursor = 'pointer';
      } else {
        setHoveredPlanet(null);
        setTooltipPos(null);
        renderer.domElement.style.cursor = 'grab';
      }
    };

    const onClick = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(interactableObjects);

      if (intersects.length > 0) {
        const hitPlanet = intersects[0].object.userData.planet as PlanetModel;
        setActiveTelemetryPlanetName(hitPlanet.name);
        setHighlightPlanetName(hitPlanet.name);
      }
    };

    const domEl = renderer.domElement;
    domEl.addEventListener('mousemove', onMouseMove);
    domEl.addEventListener('click', onClick);

    // 7. Animation Loop
    let animFrameId: number;

    const animate = () => {
      animFrameId = requestAnimationFrame(animate);

      starMesh.rotation.y += 0.002;

      if (!isPaused) {
        planetMeshes.forEach((pObj) => {
          pObj.angle += pObj.speed * orbitSpeed;
          pObj.mesh.position.x = Math.cos(pObj.angle) * pObj.orbitRadius;
          pObj.mesh.position.z = Math.sin(pObj.angle) * pObj.orbitRadius;
          pObj.mesh.rotation.y += 0.015 * orbitSpeed;
        });
      }

      controls.update();
      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = Math.max(580, container.clientHeight);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animFrameId);
      domEl.removeEventListener('mousemove', onMouseMove);
      domEl.removeEventListener('click', onClick);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, [activeSystem, highlightPlanetName, isPaused, orbitSpeed]);

  // Camera Preset Actions
  const handlePreset3D = () => {
    if (cameraRef.current && controlsRef.current) {
      const maxSma = Math.max(...activeSystem.planets.map((p) => p.sma || 0.1), activeSystem.hzOuter, 0.1);
      const scaleFactor = 28 / maxSma;
      cameraRef.current.position.set(0, Math.max(16, maxSma * scaleFactor * 0.6), Math.max(26, maxSma * scaleFactor * 1.3));
      controlsRef.current.target.set(0, 0, 0);
    }
  };

  const handlePresetTopDown = () => {
    if (cameraRef.current && controlsRef.current) {
      cameraRef.current.position.set(0, 65, 0.01);
      controlsRef.current.target.set(0, 0, 0);
    }
  };

  const handlePresetEdgeOn = () => {
    if (cameraRef.current && controlsRef.current) {
      cameraRef.current.position.set(0, 1.2, 55);
      controlsRef.current.target.set(0, 0, 0);
    }
  };

  return (
    <div className="animate-fade-in space-y-6">
      {/* ── System Selector Card ── */}
      <div className="glass-card p-5 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <h2 className="text-base font-bold text-text tracking-wide">Select Planetary System</h2>
        </div>

        {/* Row 1: Search input + Category Filter */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-3">
            <label className="text-xs text-text-muted block mb-1.5 font-medium">
              Search by Star or Planet Name (e.g. Kepler-452, TOI-700, TRAPPIST-1, 10007916)
            </label>
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Type host or planet name..."
                className="w-full px-4 py-2 text-sm bg-surface border border-surface-border rounded-xl text-text focus:outline-none focus:border-gold/50 transition-colors"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-text-muted hover:text-text"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          <div className="md:col-span-1">
            <label className="text-xs text-text-muted block mb-1.5 font-medium">Filter systems</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-surface border border-surface-border rounded-xl text-text focus:outline-none focus:border-gold/50 cursor-pointer"
            >
              <option value="Top Habitable Systems">Top Habitable Systems</option>
              <option value="Multi-Planet Systems">Multi-Planet Systems</option>
              <option value="All Systems (Search)">All Systems (Search)</option>
            </select>
          </div>
        </div>

        {/* Row 2: Choose Star System to Visualize Dropdown */}
        <div>
          <label className="text-xs text-text-muted block mb-1.5 font-medium">
            Choose Star System to Visualize:
          </label>
          <select
            value={selectedHostName}
            onChange={(e) => {
              setSelectedHostName(e.target.value);
              setHighlightPlanetName('(None / Show All)');
              setActiveTelemetryPlanetName('');
            }}
            className="w-full px-4 py-2.5 text-sm bg-surface border border-surface-border rounded-xl text-text font-semibold focus:outline-none focus:border-gold/50 cursor-pointer"
          >
            {filteredHostNames.map((host) => {
              const count = systemMap.get(host)?.length || 1;
              return (
                <option key={host} value={host}>
                  {host} ({count} planet{count > 1 ? 's' : ''})
                </option>
              );
            })}
          </select>
        </div>

        {/* Row 3: Highlight Planet + Camera Presets */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pt-1">
          <div className="flex-1 max-w-md">
            <label className="text-xs text-text-muted block mb-1.5 font-medium">
              Highlight Planet in 3D Model:
            </label>
            <select
              value={highlightPlanetName}
              onChange={(e) => {
                setHighlightPlanetName(e.target.value);
                if (e.target.value !== '(None / Show All)') {
                  setActiveTelemetryPlanetName(e.target.value);
                }
              }}
              className="w-full px-3 py-1.5 text-xs bg-surface border border-surface-border rounded-lg text-text focus:outline-none focus:border-gold/40 cursor-pointer"
            >
              <option value="(None / Show All)">(None / Show All)</option>
              {activeSystem.planets.map((p) => (
                <option key={p.id} value={p.name}>
                  {p.name} {p.inHz ? '[IN HZ]' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs text-text-muted block mb-1.5 font-medium">
              Camera View Presets:
            </label>
            <div className="flex items-center gap-2">
              <button
                onClick={handlePreset3D}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-surface hover:bg-white/10 border border-surface-border text-text transition-colors"
              >
                <Orbit className="w-3.5 h-3.5 text-teal" />
                <span>3D Orbit</span>
              </button>
              <button
                onClick={handlePresetTopDown}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-surface hover:bg-white/10 border border-surface-border text-text transition-colors"
              >
                <Eye className="w-3.5 h-3.5 text-gold" />
                <span>Top-Down (Plane)</span>
              </button>
              <button
                onClick={handlePresetEdgeOn}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-surface hover:bg-white/10 border border-surface-border text-text transition-colors"
              >
                <Globe2 className="w-3.5 h-3.5 text-status-success" />
                <span>Edge-On (Transit)</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Real-time WebGL Simulation ───────────────────────────── */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-bold text-text uppercase tracking-wide">
            Real-time WebGL Simulation (Drag to Orbit, Scroll to Zoom)
          </h3>
        </div>

        <div className="relative glass-card overflow-hidden rounded-2xl border border-surface-border/60 bg-[#00050a]">
          {/* Three.js Simulation Canvas */}
          <div ref={containerRef} className="w-full h-[580px] cursor-grab active:cursor-grabbing block" />

          {/* Interactive Hover Tooltip */}
          {hoveredPlanet && tooltipPos && (
            <div
              className="absolute z-30 p-3.5 rounded-xl bg-[#090e1c]/95 border border-gold/50 shadow-2xl backdrop-blur-md w-64 pointer-events-none text-xs font-mono animate-fade-in"
              style={{
                left: Math.min(tooltipPos.x + 15, (containerRef.current?.clientWidth || 800) - 270),
                top: Math.min(tooltipPos.y + 15, (containerRef.current?.clientHeight || 580) - 180),
              }}
            >
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-surface-border">
                <span className="font-bold text-text text-sm font-sans">{hoveredPlanet.name}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-sans font-bold ${hoveredPlanet.inHz ? 'bg-status-success/20 text-status-success' : 'bg-surface text-text-muted'}`}>
                  {hoveredPlanet.inHz ? 'IN HZ' : 'OUTSIDE HZ'}
                </span>
              </div>
              <div className="space-y-1 text-text-muted text-[11px]">
                <p>• Orbit: <strong className="text-text">{hoveredPlanet.sma.toFixed(4)} AU</strong> ({hoveredPlanet.period.toFixed(1)} d)</p>
                <p>• Radius: <strong className="text-text">{hoveredPlanet.radius.toFixed(2)} R⊕</strong></p>
                <p>• Temp: <strong className="text-text">{hoveredPlanet.temp.toFixed(0)} K</strong></p>
                <p>• Climate: <strong className="text-gold">{hoveredPlanet.climate}</strong></p>
              </div>
            </div>
          )}

          {/* Orbit Speed Slider Capsule */}
          <div className="absolute bottom-5 left-1/2 -translate-x-1/2 z-20 flex items-center gap-3 bg-[#0a0f1d]/90 px-4 py-2 rounded-2xl border border-gold/30 shadow-2xl backdrop-blur-md">
            <button
              onClick={() => setIsPaused(!isPaused)}
              className="p-1.5 rounded-lg bg-surface hover:bg-white/10 text-gold transition-colors"
              title={isPaused ? 'Resume Orbit Simulation' : 'Pause Orbit Simulation'}
            >
              {isPaused ? <Play className="w-4 h-4 fill-current" /> : <Pause className="w-4 h-4 fill-current" />}
            </button>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gold font-bold font-mono">Orbit Speed</span>
              <input
                type="range"
                min="0"
                max="5"
                step="0.1"
                value={orbitSpeed}
                onChange={(e) => setOrbitSpeed(parseFloat(e.target.value))}
                className="w-36 accent-blue-500 cursor-pointer"
              />
              <span className="text-xs font-mono font-bold text-text w-8">{orbitSpeed.toFixed(1)}x</span>
            </div>
            <button
              onClick={() => setOrbitSpeed(1.0)}
              className="p-1 rounded-md text-text-muted hover:text-text"
              title="Reset Speed"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* ── 3D Model Legend Bar ── */}
      <div className="p-3.5 rounded-xl bg-[#0d1222]/80 border border-surface-border text-xs flex items-center gap-6 flex-wrap font-medium">
        <span className="text-text font-bold">3D Model Legend:</span>
        <span className="text-[#ffd32a]">Central Glowing Sun</span>
        <span className="text-[#2ed573]">Green Disc = Conservative Habitable Zone (Liquid Water)</span>
        <span className="text-[#00d2d3]">Cyan Disc = Optimistic Habitable Zone</span>
        <span className="text-[#ff4757]">Red Reticle = Highlighted Planet</span>
      </div>

      {/* ── Astrobiology & Planetary Science Inferences Deck ─────── */}
      {activeTelemetryPlanet && (
        <div className="space-y-4 pt-2">
          <div className="border-t border-surface-border pt-4">
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-gold" />
              <h3 className="text-lg font-bold text-text tracking-wide">
                Astrobiology & Planetary Science Inferences
              </h3>
            </div>
            <p className="text-xs text-text-muted mt-0.5">
              Deep physical modeling for astrobiological assessment and atmospheric characterization feasibility:
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">
            {/* 3D Climate Globe */}
            <div className="lg:col-span-2 glass-card p-5 flex flex-col items-center justify-center text-center">
              <div className="w-full text-left mb-1">
                <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                  3D Climate Globe: {activeTelemetryPlanet.name}
                </h4>
                <p className="text-xs font-medium text-gold mt-0.5">
                  {activeTelemetryPlanet.climate}
                </p>
              </div>
              <AnimatedClimateGlobe planet={activeTelemetryPlanet} />
              <div className="w-full flex items-center justify-between text-[10px] text-text-muted pt-2 border-t border-surface-border/40 font-mono">
                <span>3D Surface Thermal Model</span>
                <span>{activeTelemetryPlanet.temp.toFixed(0)} K Surface Eq.</span>
              </div>
            </div>

            {/* Telemetry Details */}
            <div className="lg:col-span-3 glass-card p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xl font-bold text-text tracking-wide flex items-center gap-2">
                  <span>Telemetry: {activeTelemetryPlanet.name}</span>
                </h4>
                <span className={`px-2.5 py-1 text-xs font-semibold rounded-md border ${
                  activeTelemetryPlanet.status === 'CONFIRMED'
                    ? 'bg-status-success/10 text-status-success border-status-success/30'
                    : 'bg-gold/10 text-gold border-gold/30'
                }`}>
                  {activeTelemetryPlanet.status === 'CONFIRMED' ? 'CONFIRMED PLANET' : 'CANDIDATE'}
                </span>
              </div>

              {activeTelemetryPlanet.inHz ? (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-status-success/10 border border-status-success/30 text-status-success text-sm font-semibold">
                  <span>Inside Conservative Habitable Zone (Liquid Surface Water Feasible)</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-[#1e2330] border border-surface-border text-[#f59e0b] text-sm font-semibold">
                  <span>Outside Habitable Zone</span>
                </div>
              )}

              <div className="p-4 rounded-xl bg-[#090e1a]/80 border border-indigo-500/25 space-y-2 text-xs font-mono">
                <div className="flex items-center gap-2 text-text font-sans font-bold text-sm mb-2">
                  <span>Planetary Astrophysics & Atmosphere:</span>
                </div>
                <div className="space-y-1.5 leading-relaxed">
                  <p className="text-text">
                    • <span className="text-text-muted">Habitability Composite Score:</span>{' '}
                    <strong className="text-status-success">{activeTelemetryPlanet.score.toFixed(3)}</strong> / 1.000
                  </p>
                  <p className="text-text">
                    • <span className="text-text-muted">Earth Similarity Index (ESI):</span>{' '}
                    <strong className="text-status-success">{activeTelemetryPlanet.esi.toFixed(3)}</strong> / 1.000
                  </p>
                  <p className="text-text">
                    • <span className="text-text-muted">Atmospheric Retention:</span>{' '}
                    <strong className="text-blue-400">{activeTelemetryPlanet.atmRetention}</strong>
                  </p>
                  <p className="text-text">
                    • <span className="text-text-muted">Tidal Lock State:</span>{' '}
                    <strong className="text-gold">{activeTelemetryPlanet.tidalLock}</strong>
                  </p>
                  <p className="text-text">
                    • <span className="text-text-muted">Stellar UV / Flare Hazard:</span>{' '}
                    <strong className="text-status-danger">{activeTelemetryPlanet.uvHazard}</strong>
                  </p>
                  <p className="text-text">
                    • <span className="text-text-muted">Equilibrium Temperature:</span>{' '}
                    <span className="text-text font-bold">{activeTelemetryPlanet.temp.toFixed(0)} K</span> (Estimated Surface: ~{(activeTelemetryPlanet.temp + 33).toFixed(0)} K with 1 bar atm)
                  </p>
                  <p className="text-text">
                    • <span className="text-text-muted">Orbital Distance & Period:</span>{' '}
                    <span className="text-text font-bold">{activeTelemetryPlanet.sma.toFixed(4)} AU</span> ({activeTelemetryPlanet.period.toFixed(1)} days)
                  </p>
                  <p className="text-text">
                    • <span className="text-text-muted">Radius & Regime:</span>{' '}
                    <span className="text-text font-bold">{activeTelemetryPlanet.radius.toFixed(2)} R⊕</span> ({activeTelemetryPlanet.climate.split('/')[0]})
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── NASA Eyes on Exoplanets Launch Card ──────────────────── */}
      <div className="glass-card p-6 rounded-2xl border border-indigo-500/30 bg-[#090d1b]/90 shadow-2xl text-center space-y-4">
        <div className="flex items-center justify-center gap-2">
          <h3 className="text-lg font-bold text-white tracking-wide">
            NASA Eyes on Exoplanets — 3D Universe Explorer
          </h3>
        </div>
        <p className="text-xs text-text-muted max-w-xl mx-auto">
          Fly to <strong className="text-blue-400">{activeSystem.name}</strong> in NASA's official WebGL 3D simulation engine:
        </p>
        <div className="flex items-center gap-3 justify-center flex-wrap">
          <button
            onClick={() => window.open(`https://eyes.nasa.gov/apps/exo/#/star/${encodeURIComponent(activeSystem.name.replace(/\s+/g, '_'))}`, '_blank')}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs shadow-lg shadow-blue-500/25 transition-all"
          >
            <span>Fly to {activeSystem.name}</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => window.open('https://eyes.nasa.gov/apps/exo/', '_blank')}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-white font-semibold text-xs shadow-lg shadow-teal-500/25 transition-all"
          >
            <span>Open Full Universe</span>
          </button>
          <button
            onClick={() => window.open(`https://exoplanetarchive.ipac.caltech.edu/overview/${encodeURIComponent(activeSystem.name)}`, '_blank')}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-text font-semibold text-xs transition-all"
          >
            <span>NASA Archive Page</span>
          </button>
        </div>
      </div>

      {/* ── System Planetary Telemetry Table ─────────────────────── */}
      <div className="glass-card overflow-hidden">
        <div className="px-5 pt-4 pb-3 border-b border-surface-border flex items-center justify-between">
          <h3 className="section-title text-sm font-semibold tracking-wide">
            SYSTEM PLANETARY TELEMETRY TABLE: {activeSystem.name.toUpperCase()}
          </h3>
          <span className="text-xs text-text-muted font-mono">
            {activeSystem.planets.length} Planet{activeSystem.planets.length > 1 ? 's' : ''} in System
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="event-table w-full">
            <thead>
              <tr className="border-b border-surface-border">
                <th className="text-center font-mono text-text-muted text-[10px] w-10">#</th>
                <th className="text-left text-xs font-semibold text-text-muted">Planet</th>
                <th className="text-right text-xs font-semibold text-text-muted">Radius (R⊕)</th>
                <th className="text-right text-xs font-semibold text-text-muted">Period (d)</th>
                <th className="text-right text-xs font-semibold text-text-muted">Distance (AU)</th>
                <th className="text-right text-xs font-semibold text-text-muted">Temp (K)</th>
                <th className="text-right text-xs font-semibold text-text-muted">Insol (S⊕)</th>
                <th className="text-right text-xs font-semibold text-text-muted">ESI</th>
                <th className="text-left text-xs font-semibold text-text-muted pl-6">Score</th>
                <th className="text-left text-xs font-semibold text-text-muted">Climate Regime</th>
                <th className="text-center text-xs font-semibold text-text-muted pr-4">In HZ</th>
              </tr>
            </thead>
            <tbody>
              {activeSystem.planets.map((p, idx) => (
                <tr
                  key={p.id}
                  onClick={() => {
                    setActiveTelemetryPlanetName(p.name);
                    setHighlightPlanetName(p.name);
                  }}
                  className={`transition-colors cursor-pointer border-b border-surface-border/40 hover:bg-white/5 ${
                    activeTelemetryPlanet?.name === p.name ? 'bg-gold/5' : ''
                  }`}
                >
                  <td className="text-center font-mono text-text-muted text-xs font-medium py-3">{idx + 1}</td>
                  <td className="font-mono text-sm text-text font-semibold py-3 flex items-center gap-2">
                    <span className="w-2.5 h-1 rounded" style={{ backgroundColor: p.color }} />
                    {p.name}
                  </td>
                  <td className="font-mono text-sm text-text text-right py-3">{p.radius.toFixed(2)}</td>
                  <td className="font-mono text-sm text-text text-right py-3">{p.period.toFixed(2)}</td>
                  <td className="font-mono text-sm text-text text-right py-3">{p.sma.toFixed(4)}</td>
                  <td className="font-mono text-sm text-text text-right py-3">{p.temp.toFixed(0)}</td>
                  <td className="font-mono text-sm text-text text-right py-3">{p.insol.toFixed(2)}</td>
                  <td className="font-mono text-sm text-text text-right py-3">{p.esi.toFixed(3)}</td>
                  <td className="py-3 pl-6">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/5">
                        <div
                          className="h-full rounded-full transition-all duration-300"
                          style={{
                            width: `${Math.min(100, Math.max(4, (p.score || 0) * 100))}%`,
                            backgroundColor: `hsl(${Math.min(140, Math.max(0, (p.score || 0) * 140))}, 85%, 48%)`,
                          }}
                        />
                      </div>
                      <span className="text-xs font-mono text-text font-semibold">{p.score.toFixed(3)}</span>
                    </div>
                  </td>
                  <td className="text-text text-xs py-3">{p.climate}</td>
                  <td className="py-3 pr-4 text-center">
                    {p.inHz ? (
                      <span className="text-xs text-status-success font-semibold">Yes</span>
                    ) : (
                      <span className="text-xs text-text-muted">No</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
