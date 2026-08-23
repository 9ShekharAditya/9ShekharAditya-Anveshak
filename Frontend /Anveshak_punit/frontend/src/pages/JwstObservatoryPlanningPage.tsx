import { useState, useMemo } from 'react';
import {
  Microscope, Check, Search, MapPin, BarChart3, ChevronDown,
  Camera, ZoomIn, ZoomOut, Move, Home, Maximize2
} from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, ReferenceArea, ReferenceLine
} from 'recharts';

/* ─── Data Models ────────────────────────────────────────── */

interface JWSTTarget {
  id: number;
  planet: string;
  mission: 'Kepler' | 'Confirmed' | 'TESS' | 'K2';
  radiusEarth: number;
  tEqK: number;
  esi: number;
  habitabilityScore: number;
  tsm: number; // Transmission Spectroscopy Metric
  esm: number; // Emission Spectroscopy Metric
  jwstPriority: 'High Priority' | 'Priority Target' | 'Medium Priority';
  inHz: boolean;
  atmosphereStatus: string;
}

interface Observatory {
  name: string;
  location: string;
  elevation: string;
  telescope: string;
  coords: string;
  visibilityStatus: 'Optimal Night Window' | 'Partial Window' | 'Low Altitude';
  airmassMin: number;
  windowIST: string;
}

/* ─── Datasets ───────────────────────────────────────────── */

const JWST_TARGETS: JWSTTarget[] = [
  { id: 0, planet: 'K05948.01', mission: 'Kepler', radiusEarth: 1.18, tEqK: 245, esi: 0.880, habitabilityScore: 0.810, tsm: 0.7, esm: 0.2, jwstPriority: 'Priority Target', inHz: true, atmosphereStatus: 'Optimal (Water Vapor & Ozone Likely)' },
  { id: 1, planet: 'K07231.02', mission: 'Kepler', radiusEarth: 13333.50, tEqK: 1640, esi: 0.001, habitabilityScore: 0.000, tsm: 851026.6, esm: 31145066.14, jwstPriority: 'High Priority', inHz: false, atmosphereStatus: 'Strong (Dense Atmosphere Likely)' },
  { id: 2, planet: 'K05385.01', mission: 'Kepler', radiusEarth: 6815.75, tEqK: 221, esi: 0.011, habitabilityScore: 0.502, tsm: 272957.4, esm: 42056.21, jwstPriority: 'High Priority', inHz: true, atmosphereStatus: 'Strong (Dense Atmosphere Likely)' },
  { id: 3, planet: 'K05681.01', mission: 'Kepler', radiusEarth: 28199.30, tEqK: 702, esi: 0.002, habitabilityScore: 0.000, tsm: 270122.2, esm: 8668792.93, jwstPriority: 'High Priority', inHz: false, atmosphereStatus: 'Strong (Dense Atmosphere Likely)' },
  { id: 4, planet: 'K00423.02', mission: 'Kepler', radiusEarth: 11943.80, tEqK: 339, esi: 0.007, habitabilityScore: 0.105, tsm: 242874.7, esm: 463860.48, jwstPriority: 'High Priority', inHz: false, atmosphereStatus: 'Strong (Dense Atmosphere Likely)' },
  { id: 5, planet: 'K05873.01', mission: 'Kepler', radiusEarth: 109061.00, tEqK: 802, esi: 0.001, habitabilityScore: 0.000, tsm: 171709.3, esm: 18264727.92, jwstPriority: 'High Priority', inHz: false, atmosphereStatus: 'Strong (Dense Atmosphere Likely)' },
  { id: 6, planet: 'ZTF J1230-2655 b', mission: 'Confirmed', radiusEarth: 13.79, tEqK: 2950, esi: 0.032, habitabilityScore: 0.000, tsm: 83654.0, esm: 1183343.61, jwstPriority: 'High Priority', inHz: false, atmosphereStatus: 'Strong (Dense Atmosphere Likely)' },
  { id: 7, planet: 'K01250.02', mission: 'Kepler', radiusEarth: 697.14, tEqK: 1789, esi: 0.006, habitabilityScore: 0.000, tsm: 74646.0, esm: 393622.17, jwstPriority: 'High Priority', inHz: false, atmosphereStatus: 'Strong (Dense Atmosphere Likely)' },
  { id: 8, planet: 'TOI-700 d', mission: 'TESS', radiusEarth: 1.14, tEqK: 269, esi: 0.932, habitabilityScore: 0.890, tsm: 142.5, esm: 18.4, jwstPriority: 'Priority Target', inHz: true, atmosphereStatus: 'Optimal (Water Ocean Likely)' },
  { id: 9, planet: 'TRAPPIST-1 e', mission: 'Confirmed', radiusEarth: 0.92, tEqK: 251, esi: 0.850, habitabilityScore: 0.850, tsm: 98.2, esm: 12.1, jwstPriority: 'Priority Target', inHz: true, atmosphereStatus: 'Optimal (H2O / CO2 Capable)' },
  { id: 10, planet: 'K05755.01', mission: 'Kepler', radiusEarth: 1.15, tEqK: 222, esi: 0.865, habitabilityScore: 0.766, tsm: 88.4, esm: 9.8, jwstPriority: 'High Priority', inHz: true, atmosphereStatus: 'Strong (Thick Atmosphere Likely)' }
];

const INDIAN_OBSERVATORIES: Observatory[] = [
  {
    name: 'Devasthal Observatory (ARIES)',
    location: 'Nainital, Uttarakhand',
    elevation: '2,450 m',
    telescope: '3.6m Devasthal Optical Telescope (DOT)',
    coords: '29.36° N, 79.68° E',
    visibilityStatus: 'Optimal Night Window',
    airmassMin: 1.08,
    windowIST: '22:15 - 04:45 IST'
  },
  {
    name: 'Indian Astronomical Observatory (IAO)',
    location: 'Hanle, Ladakh',
    elevation: '4,500 m (High Altitude)',
    telescope: '2.0m Himalayan Chandra Telescope (HCT)',
    coords: '32.78° N, 78.96° E',
    visibilityStatus: 'Optimal Night Window',
    airmassMin: 1.04,
    windowIST: '21:30 - 05:15 IST'
  },
  {
    name: 'Vainu Bappu Observatory (VBO)',
    location: 'Kavalur, Tamil Nadu',
    elevation: '725 m',
    telescope: '2.34m Vainu Bappu Telescope (VBT)',
    coords: '12.57° N, 78.82° E',
    visibilityStatus: 'Partial Window',
    airmassMin: 1.25,
    windowIST: '23:00 - 03:30 IST'
  },
  {
    name: 'Mount Abu InfraRed Observatory (MIRO)',
    location: 'Gurushikhar, Rajasthan',
    elevation: '1,680 m',
    telescope: '1.2m & 2.5m InfraRed Telescopes',
    coords: '24.65° N, 72.78° E',
    visibilityStatus: 'Optimal Night Window',
    airmassMin: 1.12,
    windowIST: '22:00 - 04:15 IST'
  }
];

export default function JwstObservatoryPlanningPage() {
  const [activeTab, setActiveTab] = useState<'ranking' | 'simulator' | 'observatories'>('ranking');
  const [searchFilter, setSearchFilter] = useState('');
  const [onlyHz, setOnlyHz] = useState(false);

  // Selected Target for Simulator (Default: K05948.01)
  const [selectedSimPlanetId, setSelectedSimPlanetId] = useState<number>(0);

  const selectedSimPlanet = useMemo(() => {
    return JWST_TARGETS.find((t) => t.id === selectedSimPlanetId) || JWST_TARGETS[0];
  }, [selectedSimPlanetId]);

  // Filtered JWST ranking dataset
  const filteredTargets = useMemo(() => {
    return JWST_TARGETS.filter((t) => {
      const matchesSearch = t.planet.toLowerCase().includes(searchFilter.toLowerCase()) ||
                            t.mission.toLowerCase().includes(searchFilter.toLowerCase());
      const matchesHz = onlyHz ? t.inHz : true;
      return matchesSearch && matchesHz;
    });
  }, [searchFilter, onlyHz]);

  // Synthetic JWST Transit Spectrum Generator (Matching Screenshot 1 & 2)
  const spectrumData = useMemo(() => {
    const data = [];
    const baseDepth = 220.0;

    for (let w = 0.6; w <= 12.0; w += 0.05) {
      const wavelength = parseFloat(w.toFixed(2));

      // Absorption dip profiles matching exact annotated bands in screenshot
      const h2oBand1  = Math.exp(-Math.pow((wavelength - 1.4) / 0.2, 2)) * 3.8;
      const ch4Band   = Math.exp(-Math.pow((wavelength - 3.3) / 0.35, 2)) * 3.1;
      const co2Band   = Math.exp(-Math.pow((wavelength - 4.3) / 0.3, 2)) * 1.7;
      const h2oBand2  = Math.exp(-Math.pow((wavelength - 6.3) / 0.45, 2)) * 3.8;
      const o3Band    = Math.exp(-Math.pow((wavelength - 9.6) / 0.75, 2)) * 4.2;
      const nh3Band   = Math.exp(-Math.pow((wavelength - 10.5) / 0.4, 2)) * 2.8;

      const totalSignal = baseDepth + h2oBand1 + ch4Band + co2Band + h2oBand2 + o3Band + nh3Band;

      // Realistic high-frequency JWST spectrograph noise
      const noise = (Math.sin(wavelength * 65) * Math.cos(wavelength * 23) * 0.45) + (Math.random() - 0.5) * 0.35;

      data.push({
        wavelength,
        transitDepthPpm: parseFloat((totalSignal + noise).toFixed(1)),
      });
    }
    return data;
  }, [selectedSimPlanet]);

  // Histogram data for TSM distribution
  const tsmHistogramData = useMemo(() => {
    return [
      { range: '0 - 10 (Low)', count: 2, label: 'Sub-threshold' },
      { range: '10 - 100 (Rocky HZ)', count: 3, label: 'JWST Rocky Threshold' },
      { range: '100 - 1K (Sub-Neptune)', count: 4, label: 'JWST High Signal' },
      { range: '1K - 10K (Super-Earth)', count: 2, label: 'Ultra High TSM' },
      { range: '> 10K (Giant Atmosphere)', count: 5, label: 'Extreme TSM' },
    ];
  }, []);

  return (
    <div className="animate-fade-in space-y-6">
      {/* ─── Page Title Header ─── */}
      <div>
        <div className="flex items-center gap-3 mb-1">
          <Microscope className="w-6 h-6 text-gold" />
          <h1 className="text-2xl font-bold text-text tracking-wide">
            JWST Characterization & ISRO Observatory Planning
          </h1>
        </div>
        <p className="text-xs text-text-muted">
          Transit Spectroscopy Metrics (Kempton et al. 2018), synthetic biosignature spectra, and target visibility from Indian ground-based observatories
        </p>
      </div>

      {/* ─── Top Navigation Tabs (Matching Screenshot) ─── */}
      <div className="flex items-center gap-6 border-b border-surface-border/60 pb-3">
        <button
          onClick={() => setActiveTab('ranking')}
          className={`flex items-center gap-2 text-xs font-bold tracking-wider transition-all pb-1 relative ${
            activeTab === 'ranking'
              ? 'text-gold'
              : 'text-text-muted hover:text-text'
          }`}
        >
          <span>JWST Target Priority Ranking</span>
          {activeTab === 'ranking' && (
            <div className="absolute bottom-[-13px] left-0 right-0 h-0.5 bg-gold shadow-sm shadow-gold/50" />
          )}
        </button>

        <button
          onClick={() => setActiveTab('simulator')}
          className={`flex items-center gap-2 text-xs font-bold tracking-wider transition-all pb-1 relative ${
            activeTab === 'simulator'
              ? 'text-gold'
              : 'text-text-muted hover:text-text'
          }`}
        >
          <span>Biosignature Spectrum Simulator</span>
          {activeTab === 'simulator' && (
            <div className="absolute bottom-[-13px] left-0 right-0 h-0.5 bg-gold shadow-sm shadow-gold/50" />
          )}
        </button>

        <button
          onClick={() => setActiveTab('observatories')}
          className={`flex items-center gap-2 text-xs font-bold tracking-wider transition-all pb-1 relative ${
            activeTab === 'observatories'
              ? 'text-gold'
              : 'text-text-muted hover:text-text'
          }`}
        >
          <span>Indian Observatory Visibility</span>
          {activeTab === 'observatories' && (
            <div className="absolute bottom-[-13px] left-0 right-0 h-0.5 bg-gold shadow-sm shadow-gold/50" />
          )}
        </button>
      </div>

      {/* ─── TAB 1: JWST TARGET PRIORITY RANKING ─── */}
      {activeTab === 'ranking' && (
        <div className="space-y-6 animate-fade-in">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-lg font-bold text-text tracking-wide">
                JWST Follow-Up Target Priority (Kempton et al. 2018)
              </h2>
            </div>
            <p className="text-xs text-text-muted max-w-5xl leading-relaxed">
              The <strong className="text-text">Transmission Spectroscopy Metric (TSM)</strong> predicts how easily JWST can detect atmospheric features during planetary transits. Higher TSM = better target. Thresholds: <strong className="text-gold">TSM &gt; 10</strong> for rocky worlds, <strong className="text-teal">TSM &gt; 90</strong> for sub-Neptunes.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 glass-card p-3.5">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search candidate planet or mission..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="w-full bg-surface border border-surface-border rounded-lg pl-9 pr-4 py-1.5 text-xs text-text focus:outline-none focus:border-gold/40"
              />
            </div>

            <label className="flex items-center gap-2 text-xs text-text font-medium cursor-pointer select-none">
              <input
                type="checkbox"
                checked={onlyHz}
                onChange={(e) => setOnlyHz(e.target.checked)}
                className="rounded border-surface-border text-gold focus:ring-0 cursor-pointer"
              />
              <span>Filter Habitable Zone Planets Only</span>
            </label>
          </div>

          <div className="glass-card overflow-x-auto rounded-2xl border border-surface-border/60">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-surface-border/80 text-text-muted uppercase text-[10px] tracking-wider bg-[#090d16]">
                  <th className="p-3.5 w-12 text-center">#</th>
                  <th className="p-3.5 font-bold">Planet</th>
                  <th className="p-3.5">Mission</th>
                  <th className="p-3.5 text-right font-mono">Radius (R⊕)</th>
                  <th className="p-3.5 text-right font-mono">T_eq (K)</th>
                  <th className="p-3.5 text-right font-mono">ESI</th>
                  <th className="p-3.5 w-44">Habitability</th>
                  <th className="p-3.5 text-right font-mono text-gold font-bold">TSM</th>
                  <th className="p-3.5 text-right font-mono">ESM</th>
                  <th className="p-3.5">JWST Priority</th>
                  <th className="p-3.5 text-center">In HZ</th>
                  <th className="p-3.5">Atmosphere</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border/40 font-mono">
                {filteredTargets.map((row) => (
                  <tr key={row.id} className="hover:bg-white/[0.03] transition-colors">
                    <td className="p-3.5 text-center text-text-muted">{row.id}</td>
                    <td className="p-3.5 font-bold text-text font-sans">{row.planet}</td>
                    <td className="p-3.5 font-sans">
                      <span className="px-2 py-0.5 rounded bg-surface border border-surface-border text-[10px] text-text-muted">
                        {row.mission}
                      </span>
                    </td>
                    <td className="p-3.5 text-right text-text">{row.radiusEarth.toFixed(2)}</td>
                    <td className="p-3.5 text-right text-text">{row.tEqK}</td>
                    <td className="p-3.5 text-right text-text">{row.esi.toFixed(3)}</td>
                    <td className="p-3.5 font-sans">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-surface rounded-full overflow-hidden border border-surface-border/40">
                          <div
                            className={`h-full rounded-full transition-all ${
                              row.habitabilityScore > 0.7
                                ? 'bg-status-success'
                                : row.habitabilityScore > 0.4
                                ? 'bg-status-warning'
                                : 'bg-red-500/40'
                            }`}
                            style={{ width: `${Math.max(4, row.habitabilityScore * 100)}%` }}
                          />
                        </div>
                        <span className="text-[10px] font-mono text-text-muted w-10 text-right">
                          {row.habitabilityScore.toFixed(3)}
                        </span>
                      </div>
                    </td>
                    <td className="p-3.5 text-right text-gold font-bold">{row.tsm.toFixed(1)}</td>
                    <td className="p-3.5 text-right text-text-muted">{row.esm.toFixed(2)}</td>
                    <td className="p-3.5 font-sans">
                      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-status-success/10 border border-status-success/30 text-status-success text-[11px] font-semibold">
                        <span className="w-2 h-2 rounded-full bg-status-success animate-pulse"></span>
                        <span>{row.jwstPriority}</span>
                      </div>
                    </td>
                    <td className="p-3.5 text-center">
                      <div
                        className={`w-4 h-4 mx-auto rounded border flex items-center justify-center ${
                          row.inHz
                            ? 'bg-status-success/20 border-status-success text-status-success'
                            : 'border-surface-border bg-surface'
                        }`}
                      >
                        {row.inHz && <Check className="w-3 h-3 stroke-[3]" />}
                      </div>
                    </td>
                    <td className="p-3.5 font-sans text-[11px] text-text-muted">
                      {row.atmosphereStatus}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="glass-card p-6 space-y-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-gold" />
              <h3 className="text-sm font-bold text-text uppercase tracking-wide">
                TSM Distribution Across All Candidates
              </h3>
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={tsmHistogramData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="range" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
                  <RechartsTooltip contentStyle={{ backgroundColor: '#090d16', borderColor: 'rgba(255,255,255,0.15)', borderRadius: '8px' }} />
                  <Bar dataKey="count" fill="#eab308" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* ─── TAB 2: BIOSIGNATURE SPECTRUM SIMULATOR (Matching Screenshot 1 & 2) ─── */}
      {activeTab === 'simulator' && (
        <div className="space-y-6 animate-fade-in">
          {/* Header */}
          <div>
            <div className="flex items-center gap-2.5 mb-1">
              <h2 className="text-xl font-bold text-text tracking-wide">
                Simulated JWST Transit Absorption Spectrum
              </h2>
            </div>
            <p className="text-xs text-text-muted leading-relaxed max-w-5xl">
              Select a habitable candidate to simulate what <strong className="text-text">JWST NIRSpec + MIRI</strong> would observe during a transit event. Absorption dips indicate atmospheric gases — biosignatures like <strong className="text-emerald-400">O₃</strong>, <strong className="text-amber-400">CH₄</strong>, and <strong className="text-blue-400">H₂O</strong> are highlighted.
            </p>
          </div>

          {/* Select Target Dropdown Box */}
          <div className="space-y-1.5">
            <label className="text-xs text-text-muted font-medium block">
              Select target for spectral simulation:
            </label>
            <div className="relative max-w-full">
              <select
                value={selectedSimPlanetId}
                onChange={(e) => setSelectedSimPlanetId(Number(e.target.value))}
                className="w-full pr-10 pl-4 py-2.5 text-sm bg-[#090d16] border border-surface-border rounded-xl text-text font-mono font-semibold focus:outline-none focus:border-gold/40 cursor-pointer appearance-none shadow-inner"
              >
                {JWST_TARGETS.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.planet}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-text-muted absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          {/* Main Simulated JWST Spectrum Graph Container */}
          <div className="glass-card overflow-hidden rounded-2xl border border-surface-border/60 p-5 bg-[#060a12] space-y-3">
            {/* Graph Header & Plotly Modebar */}
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white font-mono tracking-wide">
                Simulated JWST Transit Spectrum: {selectedSimPlanet.planet}
              </h3>

              {/* Plotly Modebar Icons matching screenshot */}
              <div className="flex items-center gap-2 bg-[#0d121f] px-3 py-1 rounded-lg border border-surface-border/60 text-text-muted text-xs">
                <button title="Download plot as PNG" className="hover:text-text transition-colors p-0.5">
                  <Camera className="w-3.5 h-3.5" />
                </button>
                <button title="Zoom in" className="hover:text-text transition-colors p-0.5">
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
                <button title="Zoom out" className="hover:text-text transition-colors p-0.5">
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <button title="Pan mode" className="hover:text-text transition-colors p-0.5">
                  <Move className="w-3.5 h-3.5" />
                </button>
                <button title="Reset axes" className="hover:text-text transition-colors p-0.5">
                  <Home className="w-3.5 h-3.5" />
                </button>
                <button title="Toggle Fullscreen" className="hover:text-text transition-colors p-0.5">
                  <Maximize2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Recharts Absorption Spectrum Line Chart with Annotated Gas Shading */}
            <div className="h-[380px] w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={spectrumData} margin={{ top: 25, right: 25, left: 45, bottom: 25 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />

                  <XAxis
                    dataKey="wavelength"
                    domain={[0.6, 12]}
                    stroke="#94a3b8"
                    fontSize={11}
                    label={{ value: 'Wavelength (µm)', position: 'insideBottom', offset: -15, fill: '#94a3b8', fontSize: 12 }}
                  />
                  <YAxis
                    stroke="#94a3b8"
                    fontSize={11}
                    domain={['dataMin - 0.5', 'dataMax + 0.5']}
                    label={{ value: 'Transit Depth (ppm)', angle: -90, position: 'insideLeft', offset: -25, fill: '#94a3b8', fontSize: 12, style: { textAnchor: 'middle' } }}
                  />

                  <RechartsTooltip
                    contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                    formatter={(val: any) => [`Depth = ${val} ppm`, 'Transit Depth']}
                    labelFormatter={(val) => `λ = ${val} µm`}
                  />

                  {/* Instrument Region Boundaries */}
                  <ReferenceLine x={5.0} stroke="#ffffff" strokeWidth={1.5} label={{ value: 'JWST NIRSpec', fill: '#60a5fa', fontSize: 10, position: 'insideTopLeft' }} />
                  <ReferenceLine x={5.3} stroke="#ffffff" strokeWidth={1.5} label={{ value: 'JWST MIRI', fill: '#f87171', fontSize: 10, position: 'insideTopRight' }} />

                  {/* Highlighted Chemical Absorption Shaded Regions */}
                  {/* H2O (1.4 µm) */}
                  <ReferenceArea x1={1.25} x2={1.55} fill="rgba(56, 189, 248, 0.15)" />
                  <ReferenceLine x={1.4} stroke="#38bdf8" strokeDasharray="2 2" label={{ value: '↓ H₂O', fill: '#38bdf8', fontSize: 10, position: 'top' }} />

                  {/* CH4 (3.3 µm) */}
                  <ReferenceArea x1={3.1} x2={3.5} fill="rgba(245, 158, 11, 0.15)" />
                  <ReferenceLine x={3.3} stroke="#f59e0b" strokeDasharray="2 2" label={{ value: '↓ CH₄ (Methane)', fill: '#f59e0b', fontSize: 10, position: 'top' }} />

                  {/* CO2 (4.3 µm) */}
                  <ReferenceArea x1={4.1} x2={4.5} fill="rgba(239, 68, 68, 0.15)" />
                  <ReferenceLine x={4.3} stroke="#ef4444" strokeDasharray="2 2" label={{ value: '↓ CO₂', fill: '#ef4444', fontSize: 10, position: 'top' }} />

                  {/* H2O (6.3 µm) */}
                  <ReferenceArea x1={5.8} x2={6.8} fill="rgba(56, 189, 248, 0.15)" />
                  <ReferenceLine x={6.3} stroke="#38bdf8" strokeDasharray="2 2" label={{ value: '↓ H₂O', fill: '#38bdf8', fontSize: 10, position: 'top' }} />

                  {/* O3 (9.6 µm) */}
                  <ReferenceArea x1={9.1} x2={10.1} fill="rgba(74, 222, 128, 0.15)" />
                  <ReferenceLine x={9.6} stroke="#4ade80" strokeDasharray="2 2" label={{ value: '↓ O₃ (Ozone)', fill: '#4ade80', fontSize: 10, position: 'top' }} />

                  {/* NH3 (10.5 µm) */}
                  <ReferenceArea x1={10.3} x2={10.8} fill="rgba(168, 85, 247, 0.15)" />
                  <ReferenceLine x={10.5} stroke="#c084fc" strokeDasharray="2 2" label={{ value: '↓ NH₃', fill: '#c084fc', fontSize: 10, position: 'top' }} />

                  {/* Main Spectrum Line */}
                  <Line
                    type="monotone"
                    dataKey="transitDepthPpm"
                    stroke="#60a5fa"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 5, fill: '#60a5fa' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Bottom Telemetry & Biosignature Cards Grid (Matching Screenshot 1 & 2) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
            {/* Left Column Cards */}
            <div className="space-y-4">
              {/* Card 1: TSM Metric Box */}
              <div className="glass-card p-5 rounded-2xl border border-surface-border/60 bg-[#090d16] space-y-2">
                <span className="text-[10px] text-text-muted uppercase tracking-wider font-semibold block">
                  TRANSMISSION SPECTROSCOPY METRIC (TSM)
                </span>
                <p className="text-4xl font-extrabold text-white font-mono">
                  {selectedSimPlanet.tsm}
                </p>
              </div>

              {/* Card 2: Challenge Alert Banner */}
              {selectedSimPlanet.tsm < 10 ? (
                <div className="p-4 rounded-xl bg-[#2a230c] border border-amber-500/40 text-[#fcd34d] text-xs font-semibold flex items-center gap-3">
                  <span className="w-3.5 h-3.5 rounded-full bg-red-500 flex-shrink-0 animate-pulse"></span>
                  <span>Challenging target — requires stacking many transits</span>
                </div>
              ) : selectedSimPlanet.tsm >= 90 ? (
                <div className="p-4 rounded-xl bg-status-success/15 border border-status-success/40 text-status-success text-xs font-semibold flex items-center gap-3">
                  <span className="w-3.5 h-3.5 rounded-full bg-status-success flex-shrink-0 animate-pulse"></span>
                  <span>High Signal Target — single transit detection feasible!</span>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-amber-500/15 border border-amber-500/40 text-amber-300 text-xs font-semibold flex items-center gap-3">
                  <span className="w-3.5 h-3.5 rounded-full bg-amber-400 flex-shrink-0"></span>
                  <span>Moderate Target — 5 to 10 transits required for detection</span>
                </div>
              )}
            </div>

            {/* Right Column Cards */}
            <div className="space-y-4">
              {/* Card 1: Detectable Biosignatures */}
              <div className="glass-card p-5 rounded-2xl border border-surface-border/60 bg-[#090d16] space-y-3">
                <div className="flex items-center gap-2 text-text font-bold text-xs">
                  <span>Detectable Biosignatures:</span>
                </div>

                <ul className="space-y-2.5 text-xs text-text">
                  <li className="flex items-center gap-2">
                    <span><strong className="font-mono font-bold">H₂O (1.4 µm, 6.3 µm)</strong> — Water vapor</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span><strong className="font-mono font-bold">O₃ (9.6 µm)</strong> — Ozone (photosynthesis byproduct)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span><strong className="font-mono font-bold">CH₄ (3.3 µm)</strong> — Methane (biological/geological)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span><strong className="font-mono font-bold">CO₂ (4.3 µm)</strong> — Carbon dioxide</span>
                  </li>
                </ul>
              </div>

              {/* Card 2: HZ Meaningful Banner */}
              <div className="p-4 rounded-xl bg-[#0e291b] border border-emerald-500/40 text-emerald-300 text-xs font-semibold flex items-center gap-2.5">
                <div className="w-4 h-4 rounded bg-emerald-500/20 border border-emerald-400 flex items-center justify-center text-emerald-300">
                  <Check className="w-3 h-3 stroke-[3]" />
                </div>
                <span>HZ planet — biosignature detection is scientifically meaningful!</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ─── TAB 3: INDIAN OBSERVATORY VISIBILITY ─── */}
      {activeTab === 'observatories' && (
        <div className="space-y-6 animate-fade-in">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-lg font-bold text-text tracking-wide">
                Indian Ground-Based Observatory Visibility & Transit Planning
              </h2>
            </div>
            <p className="text-xs text-text-muted">
              Real-time observational feasibility, airmass minimums, and night transit windows across major Indian astronomical facilities:
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {INDIAN_OBSERVATORIES.map((obs, idx) => (
              <div key={idx} className="glass-card p-5 space-y-3.5 border border-surface-border/60 hover:border-gold/30 transition-all">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <MapPin className="w-5 h-5 text-gold flex-shrink-0" />
                    <div>
                      <h4 className="text-sm font-bold text-text">{obs.name}</h4>
                      <p className="text-[11px] text-text-muted flex items-center gap-1 mt-0.5">
                        <span>{obs.location} ({obs.coords})</span>
                      </p>
                    </div>
                  </div>
                  <span
                    className={`px-2.5 py-1 text-[10px] font-semibold rounded-md border ${
                      obs.visibilityStatus === 'Optimal Night Window'
                        ? 'bg-status-success/10 text-status-success border-status-success/30'
                        : 'bg-gold/10 text-gold border-gold/30'
                    }`}
                  >
                    {obs.visibilityStatus}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-surface-border/40 font-mono">
                  <div className="bg-surface/60 p-2.5 rounded-lg border border-surface-border/40">
                    <span className="text-[9px] text-text-muted uppercase block font-sans font-medium">Telescope Specs</span>
                    <strong className="text-text font-sans text-xs">{obs.telescope}</strong>
                  </div>
                  <div className="bg-surface/60 p-2.5 rounded-lg border border-surface-border/40">
                    <span className="text-[9px] text-text-muted uppercase block font-sans font-medium">Elevation</span>
                    <strong className="text-teal font-sans text-xs">{obs.elevation}</strong>
                  </div>
                  <div className="bg-surface/60 p-2.5 rounded-lg border border-surface-border/40">
                    <span className="text-[9px] text-text-muted uppercase block font-sans font-medium">Transit Window (IST)</span>
                    <strong className="text-gold font-sans text-xs">{obs.windowIST}</strong>
                  </div>
                  <div className="bg-surface/60 p-2.5 rounded-lg border border-surface-border/40">
                    <span className="text-[9px] text-text-muted uppercase block font-sans font-medium">Min. Airmass (X)</span>
                    <strong className="text-status-success font-sans text-xs">{obs.airmassMin} X</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
