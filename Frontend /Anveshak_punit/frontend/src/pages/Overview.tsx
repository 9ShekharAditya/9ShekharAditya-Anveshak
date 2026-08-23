import { useMemo, useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Target, Globe2, Orbit, Telescope, Rocket, Check, Trophy
} from 'lucide-react';
import { DATASET_OPTIONS } from '../components/TelescopeAdapterSource';

interface HabitableCandidate {
  id: string;
  planet: string;
  mission: string;
  radius: number;
  temp: number;
  insol: number;
  esi: number;
  score: number;
  sizeClass: string;
  tidalLock: string;
  inHz: boolean;
}

interface OutletContextType {
  selectedDataset: string;
  setSelectedDataset: (dataset: string) => void;
}

export default function Overview() {
  const [allHabitableCandidates, setAllHabitableCandidates] = useState<HabitableCandidate[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const context = useOutletContext<OutletContextType>();
  const selectedDataset = context?.selectedDataset || 'all';

  useEffect(() => {
    fetch('/api/v1/science/candidates')
      .then(res => res.json())
      .then(data => {
        if (data && Array.isArray(data.candidates)) {
          setAllHabitableCandidates(data.candidates);
          setIsLoading(false);
        } else {
          console.error("API returned invalid data", data);
          setErrorMsg('API returned invalid data');
          setIsLoading(false);
        }
      })
      .catch(err => { console.error(err); setErrorMsg(String(err)); setIsLoading(false); });
  }, []);

  const currentDatasetConfig = useMemo(() => {
    return DATASET_OPTIONS.find((opt) => opt.id === selectedDataset) || DATASET_OPTIONS[0];
  }, [selectedDataset]);

  const filteredCandidates = useMemo(() => {
    if (selectedDataset === 'all') return allHabitableCandidates;
    if (selectedDataset === 'kepler') return allHabitableCandidates.filter((c) => c.mission === 'Kepler');
    if (selectedDataset === 'tess') return allHabitableCandidates.filter((c) => c.mission === 'TESS');
    if (selectedDataset === 'k2') return allHabitableCandidates.filter((c) => c.mission === 'K2');
    if (selectedDataset === 'confirmed') return allHabitableCandidates.filter((c) => c.mission === 'Confirmed');
    return allHabitableCandidates;
  }, [selectedDataset, allHabitableCandidates]);

  const statCards = useMemo(() => {
    const total = filteredCandidates.length.toLocaleString();
    const inHz = filteredCandidates.filter(c => c.inHz).length.toLocaleString();
    const highPotential = filteredCandidates.filter(c => (c.score || 0) >= 0.6).length.toLocaleString();
    const earthLike = filteredCandidates.filter(c => (c.esi || 0) >= 0.8).length.toLocaleString();

    return [
      { icon: Globe2, label: 'Total Candidates', value: total, color: 'text-gold' },
      { icon: Orbit, label: 'In Habitable Zone', value: inHz, color: 'text-teal' },
      { icon: Target, label: 'High Habitability (Score ≥ 0.6)', value: highPotential, color: 'text-status-success' },
      { icon: Telescope, label: 'Earth-like (ESI ≥ 0.8)', value: earthLike, color: 'text-gold' },
    ];
  }, [filteredCandidates]);

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Rocket className="w-4 h-4 text-gold" />
            <h2 className="text-lg font-bold text-text tracking-wide">MISSION OVERVIEW</h2>
          </div>
          <p className="text-xs text-text-muted">
            Analysis and ranking of detected exoplanet candidates based on Earth Similarity Index (ESI) - [{currentDatasetConfig.name}]
          </p>
        </div>
      </div>

      {/* Main Layout */}
      <div className="space-y-5">
        {/* Stat Cards */}
        <div className="grid grid-cols-4 gap-3">
          {statCards.map((card) => {
            const Icon = card.icon;
            return (
              <div key={card.label} className="stat-card animate-slide-up">
                <div className="relative z-10">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-7 h-7 rounded-lg bg-surface-light border border-surface-border flex items-center justify-center">
                      <Icon className={`w-3.5 h-3.5 ${card.color}`} />
                    </div>
                    <span className="text-[9px] text-text-muted uppercase tracking-wider font-medium leading-tight">
                      {card.label}
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-text font-mono tracking-tight">
                    {card.value}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Top Habitable Candidates Table */}
        <div className="glass-card overflow-hidden">
          <div className="flex items-center justify-between px-5 pt-4 pb-3">
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-gold" />
              <h3 className="section-title text-sm font-semibold tracking-wide">
                MOST HABITABLE CANDIDATES ({currentDatasetConfig.name.toUpperCase()})
              </h3>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-text-muted font-mono">
                Total analyzed: {filteredCandidates.length.toLocaleString()}
              </span>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="event-table w-full">
              <thead>
                <tr className="border-b border-surface-border">
                  <th className="text-center font-mono text-text-muted text-[10px] w-10">#</th>
                  <th className="text-left text-xs font-semibold text-text-muted">Planet</th>
                  <th className="text-left text-xs font-semibold text-text-muted">Mission</th>
                  <th className="text-right text-xs font-semibold text-text-muted">Radius (R⊕)</th>
                  <th className="text-right text-xs font-semibold text-text-muted">Temp (K)</th>
                  <th className="text-right text-xs font-semibold text-text-muted">Insol (S⊕)</th>
                  <th className="text-right text-xs font-semibold text-text-muted">ESI</th>
                  <th className="text-left text-xs font-semibold text-text-muted pl-6">Score</th>
                  <th className="text-left text-xs font-semibold text-text-muted">Size Class</th>
                  <th className="text-left text-xs font-semibold text-text-muted">Tidal Lock</th>
                  <th className="text-center text-xs font-semibold text-text-muted pr-4">In HZ</th>
                </tr>
              </thead>
              <tbody>
                {filteredCandidates.map((item, idx) => (
                  <tr key={item.id} className="transition-colors cursor-pointer border-b border-surface-border/40 hover:bg-white/2">
                    <td className="text-center font-mono text-text-muted text-xs font-medium py-3">{idx}</td>
                    <td className="font-mono text-sm text-text font-semibold py-3">{item.planet}</td>
                    <td className="text-text-muted text-xs py-3">{item.mission}</td>
                    <td className="font-mono text-sm text-text text-right py-3">{(item.radius || 0).toFixed(2)}</td>
                    <td className="font-mono text-sm text-text text-right py-3">{item.temp}</td>
                    <td className="font-mono text-sm text-text text-right py-3">{(item.insol || 0).toFixed(3)}</td>
                    <td className="font-mono text-sm text-text text-right py-3">{(item.esi || 0).toFixed(3)}</td>
                    <td className="py-3 pl-6">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/5">
                          <div
                            className="h-full rounded-full transition-all duration-300"
                            style={{
                              width: `${Math.min(100, Math.max(4, (item.score || 0) * 100))}%`,
                              backgroundColor: `hsl(${Math.min(140, Math.max(0, (item.score || 0) * 140))}, 85%, 48%)`,
                            }}
                          ></div>
                        </div>
                        <span className="text-xs font-mono text-text font-semibold">{(item.score || 0).toFixed(3)}</span>
                      </div>
                    </td>
                    <td className="text-text text-xs py-3">{item.sizeClass}</td>
                    <td className="text-text-muted text-xs py-3">{item.tidalLock}</td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center justify-center">
                        <div className="w-4 h-4 rounded bg-surface-light border border-surface-border flex items-center justify-center">
                          <Check className="w-3 h-3 text-text-muted" />
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
