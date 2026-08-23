import { useState, useMemo } from 'react';
import { Globe2, Layers, Eye, Info } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
  ReferenceLine
} from 'recharts';

// Define the type for our spectrum data points
interface SpectrumDataPoint {
  wavelength: number;
  depth: number;
  error: number;
  modelClear: number;
  modelWater: number;
}

// Planets available for analysis
const planets = [
  { id: 'toi-7892b', name: 'TOI-7892 b', radius: '1.8 R⊕', starRadius: '0.9 R☉', distance: '120 pc', type: 'Hot Super-Earth' },
  { id: 'wasp-39b', name: 'WASP-39 b', radius: '1.27 R_J', starRadius: '0.93 R☉', distance: '215 pc', type: 'Hot Saturn' },
  { id: 'koi-8821', name: 'KOI-8821.01', radius: '2.3 R⊕', starRadius: '1.1 R☉', distance: '450 pc', type: 'Warm Sub-Neptune' }
];

// Chemical absorption bands (wavelength in microns)
const absorptionBands = [
  { name: 'Na (Sodium)', start: 0.55, end: 0.62, color: 'rgba(200,164,92,0.15)', textColor: '#c8a45c', peak: 0.589 },
  { name: 'H₂O (Water)', start: 1.3, end: 1.5, color: 'rgba(45,212,191,0.15)', textColor: '#2dd4bf', peak: 1.4 },
  { name: 'CH₄ (Methane)', start: 2.2, end: 2.4, color: 'rgba(245,158,11,0.15)', textColor: '#f59e0b', peak: 2.3 },
  { name: 'CO₂ (Carbon Dioxide)', start: 4.1, end: 4.5, color: 'rgba(239,68,68,0.15)', textColor: '#ef4444', peak: 4.3 }
];

export default function TransmissionSpectrumPage() {
  const [selectedPlanet, setSelectedPlanet] = useState(planets[0]);
  const [activeModel, setActiveModel] = useState<'none' | 'clear' | 'water'>('water');
  const [showBands, setShowBands] = useState(true);
  const [hazeFactor, setHazeFactor] = useState(1.0);

  // Generate simulated spectral data based on selection and parameters
  const spectrumData = useMemo<SpectrumDataPoint[]>(() => {
    const data: SpectrumDataPoint[] = [];
    const baseDepth = selectedPlanet.id === 'wasp-39b' ? 21000 : selectedPlanet.id === 'koi-8821' ? 8500 : 12000;
    
    // Generate data from 0.4 to 5.0 microns
    for (let w = 0.4; w <= 5.0; w += 0.05) {
      const wavelength = parseFloat(w.toFixed(2));
      
      // Calculate model absorption profiles
      // Sodium peak around 0.59
      const sodiumAbs = Math.exp(-Math.pow((wavelength - 0.589) / 0.03, 2)) * 800;
      
      // Water peaks around 1.4, 1.9, 2.7
      const waterAbs = (
        Math.exp(-Math.pow((wavelength - 1.4) / 0.08, 2)) * 1200 +
        Math.exp(-Math.pow((wavelength - 1.9) / 0.1, 2)) * 1500 +
        Math.exp(-Math.pow((wavelength - 2.7) / 0.15, 2)) * 1800
      );

      // Rayleigh scattering slope at shorter wavelengths modulated by haze factor
      const rayleigh = (Math.pow(0.5 / wavelength, 4) * 1500) * hazeFactor;
      
      // Methane peak around 2.3
      const methaneAbs = Math.exp(-Math.pow((wavelength - 2.3) / 0.08, 2)) * 900;
      
      // CO2 peak around 4.3
      const co2Abs = Math.exp(-Math.pow((wavelength - 4.3) / 0.12, 2)) * 2500;

      const modelClearVal = baseDepth + rayleigh + sodiumAbs + waterAbs + methaneAbs + co2Abs;
      const modelWaterVal = baseDepth + (rayleigh * 0.5) + (waterAbs * 1.2) + (co2Abs * 1.1);

      // Noise generation
      const noise = (Math.sin(wavelength * 30) * Math.cos(wavelength * 12) * 200) + (Math.random() - 0.5) * 150;
      
      const observedDepth = (activeModel === 'clear' ? modelClearVal : modelWaterVal) + noise;
      
      data.push({
        wavelength,
        depth: Math.round(observedDepth),
        error: 80,
        modelClear: Math.round(modelClearVal),
        modelWater: Math.round(modelWaterVal)
      });
    }
    return data;
  }, [selectedPlanet, activeModel, hazeFactor]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-surface-border pb-5">
        <div>
          <h1 className="text-2xl font-bold text-text flex items-center gap-2">
            <Globe2 className="w-6 h-6 text-gold" />
            Exoplanet Transmission Spectrum
          </h1>
          <p className="text-sm text-text-muted mt-1">
            Analyze atmospheric chemical composition and transit depth variations across wavelengths
          </p>
        </div>

        {/* Planet Selector */}
        <div className="flex items-center gap-3">
          <span className="text-sm text-text-muted font-medium">Target:</span>
          <select
            value={selectedPlanet.id}
            onChange={(e) => {
              const p = planets.find(item => item.id === e.target.value);
              if (p) setSelectedPlanet(p);
            }}
            className="bg-surface border border-surface-border text-text rounded-lg px-3 py-2 text-sm font-semibold focus:outline-none focus:border-gold/50"
          >
            {planets.map(p => (
              <option key={p.id} value={p.id}>{p.name} ({p.type})</option>
            ))}
          </select>
        </div>
      </div>

      {/* Target Info Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-4">
          <span className="text-xs text-text-muted block">Planet Radius</span>
          <span className="text-lg font-bold text-text font-mono mt-1 block">{selectedPlanet.radius}</span>
        </div>
        <div className="glass-card p-4">
          <span className="text-xs text-text-muted block">Stellar Radius</span>
          <span className="text-lg font-bold text-text font-mono mt-1 block">{selectedPlanet.starRadius}</span>
        </div>
        <div className="glass-card p-4">
          <span className="text-xs text-text-muted block">Distance</span>
          <span className="text-lg font-bold text-text font-mono mt-1 block">{selectedPlanet.distance}</span>
        </div>
        <div className="glass-card p-4">
          <span className="text-xs text-text-muted block">Classification</span>
          <span className="text-lg font-bold text-teal mt-1 block">{selectedPlanet.type}</span>
        </div>
      </div>

      {/* Main Chart Section */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-gold" />
            <h2 className="text-base font-semibold text-text">Transit Depth (ppm) vs. Wavelength (μm)</h2>
          </div>

          {/* Controls */}
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <label className="flex items-center gap-2 text-text cursor-pointer">
              <input
                type="checkbox"
                checked={showBands}
                onChange={(e) => setShowBands(e.target.checked)}
                className="rounded border-surface-border text-gold focus:ring-0"
              />
              Show Absorption Bands
            </label>

            <div className="flex items-center gap-2">
              <span className="text-text-muted">Model:</span>
              <button
                onClick={() => setActiveModel('water')}
                className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                  activeModel === 'water' ? 'bg-teal text-bg font-bold' : 'bg-surface border border-surface-border text-text-muted'
                }`}
              >
                Water-Rich
              </button>
              <button
                onClick={() => setActiveModel('clear')}
                className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                  activeModel === 'clear' ? 'bg-gold text-bg font-bold' : 'bg-surface border border-surface-border text-text-muted'
                }`}
              >
                Clear Atmosphere
              </button>
            </div>
          </div>
        </div>

        {/* Haze slider */}
        <div className="flex items-center gap-4 bg-surface/50 p-3 rounded-lg border border-surface-border/50 text-xs">
          <span className="text-text-muted font-medium">Aerosol / Haze Factor:</span>
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={hazeFactor}
            onChange={(e) => setHazeFactor(parseFloat(e.target.value))}
            className="w-48 accent-gold cursor-pointer"
          />
          <span className="font-mono text-gold font-bold">{hazeFactor.toFixed(1)}x</span>
          <span className="text-text-muted text-[11px] italic ml-auto">Simulates high-altitude scattering slope</span>
        </div>

        {/* Recharts Component */}
        <div className="h-[420px] w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={spectrumData} margin={{ top: 20, right: 30, left: 45, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis
                dataKey="wavelength"
                label={{ value: 'Wavelength (μm)', position: 'insideBottom', offset: -10, fill: '#94a3b8', fontSize: 12 }}
                stroke="#94a3b8"
              />
              <YAxis
                label={{ value: 'Transit Depth (ppm)', angle: -90, position: 'insideLeft', offset: -25, fill: '#94a3b8', fontSize: 12, style: { textAnchor: 'middle' } }}
                stroke="#94a3b8"
                domain={['auto', 'auto']}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                labelFormatter={(val) => `Wavelength: ${val} μm`}
              />

              {/* Absorption Band Background Regions */}
              {showBands && absorptionBands.map((band) => (
                <ReferenceArea
                  key={band.name}
                  x1={band.start}
                  x2={band.end}
                  fill={band.color}
                  strokeOpacity={0.3}
                />
              ))}

              {/* Reference Lines for Band Peaks */}
              {showBands && absorptionBands.map((band) => (
                <ReferenceLine
                  key={`line-${band.name}`}
                  x={band.peak}
                  stroke={band.textColor}
                  strokeDasharray="3 3"
                  label={{ value: band.name, fill: band.textColor, fontSize: 10, position: 'top' }}
                />
              ))}

              {/* Observed Spectrum Data Line */}
              <Line
                type="monotone"
                dataKey="depth"
                stroke="#38bdf8"
                strokeWidth={2}
                dot={{ r: 2, fill: '#38bdf8' }}
                name="Observed Depth"
              />

              {/* Active Model Overlay */}
              {activeModel === 'water' && (
                <Line
                  type="monotone"
                  dataKey="modelWater"
                  stroke="#2dd4bf"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  dot={false}
                  name="Water-Rich Model"
                />
              )}
              {activeModel === 'clear' && (
                <Line
                  type="monotone"
                  dataKey="modelClear"
                  stroke="#eab308"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  dot={false}
                  name="Clear Model"
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Spectral Feature Legend & Insights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-5 col-span-2 space-y-3">
          <h3 className="text-sm font-semibold text-text flex items-center gap-2">
            <Info className="w-4 h-4 text-gold" />
            Detected Atmospheric Species
          </h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            {absorptionBands.map((band) => (
              <div key={band.name} className="p-3 rounded-lg bg-surface/60 border border-surface-border/60 flex items-center justify-between">
                <div>
                  <span className="font-bold text-text block">{band.name}</span>
                  <span className="text-text-muted text-[11px] font-mono">{band.start} - {band.end} μm</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-teal/10 text-teal border border-teal/20">
                  Detected
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-5 space-y-3">
          <h3 className="text-sm font-semibold text-text flex items-center gap-2">
            <Eye className="w-4 h-4 text-teal" />
            Spectral Insights
          </h3>
          <p className="text-xs text-text-muted leading-relaxed">
            Strong absorption features detected around 1.4 μm and 1.9 μm indicate significant atmospheric water vapor. Short-wavelength slope suggests moderate cloud/haze scattering.
          </p>
        </div>
      </div>
    </div>
  );
}
