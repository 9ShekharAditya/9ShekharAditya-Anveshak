import { useState, useMemo, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';

interface OutletContextType {
  selectedDataset: string;
  setSelectedDataset: (dataset: string) => void;
}

/* ─── Data ──────────────────────────────────────────── */

interface Candidate {
  id: number;
  planet: string;
  mission: string;
  sizeClass: string;
  radius: number;
  period: number;
  temp: number;
  insol: number;
  esi: number;
  score: number;
  tidalLock: string;
}

type SortKey = 'score' | 'esi' | 'temp' | 'radius' | 'period' | 'insol' | 'planet';

const sortOptions: { value: SortKey; label: string }[] = [
  { value: 'score', label: 'Habitability Score' },
  { value: 'esi', label: 'ESI' },
  { value: 'temp', label: 'Temperature' },
  { value: 'radius', label: 'Radius' },
  { value: 'period', label: 'Orbital Period' },
  { value: 'insol', label: 'Insolation' },
  { value: 'planet', label: 'Planet Name' },
];

/* ─── Component ─────────────────────────────────────── */

export default function CandidatesList() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortKey>('score');
  const [ascending, setAscending] = useState(false);

  const context = useOutletContext<OutletContextType>();
  const selectedDataset = context?.selectedDataset || 'all';

  useEffect(() => {
    fetch('/api/v1/science/candidates')
      .then(res => res.json())
      .then(data => {
        if (data && Array.isArray(data.candidates)) {
          setCandidates(data.candidates);
          setIsLoading(false);
        } else {
          console.error('API returned invalid data', data);
          setErrorMsg('API returned invalid data');
          setIsLoading(false);
        }
      })
      .catch(err => { console.error(err); setErrorMsg(String(err)); setIsLoading(false); });
  }, []);

  const filteredCandidates = useMemo(() => {
    if (selectedDataset === 'all') return candidates;
    if (selectedDataset === 'kepler') return candidates.filter((c) => c.mission === 'Kepler');
    if (selectedDataset === 'tess') return candidates.filter((c) => c.mission === 'TESS');
    if (selectedDataset === 'k2') return candidates.filter((c) => c.mission === 'K2');
    if (selectedDataset === 'confirmed') return candidates.filter((c) => c.mission === 'Confirmed');
    return candidates;
  }, [selectedDataset, candidates]);

  const sorted = useMemo(() => {
    const copy = [...filteredCandidates];
    copy.sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      return ascending ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number);
    });
    return copy;
  }, [sortBy, ascending, filteredCandidates]);

  return (
    <div className="animate-fade-in space-y-4">
      {/* Subtitle */}
      <p className="text-xs text-text-muted italic">
        Filter and explore all unconfirmed exoplanet candidates
      </p>

      {/* Controls Row */}
      <div className="flex items-center gap-4 flex-wrap">
        {/* Sort Dropdown */}
        <div className="flex-1 min-w-[240px] max-w-[480px]">
          <label className="text-[10px] text-text-muted uppercase tracking-wider block mb-1">Sort by</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortKey)}
            className="w-full px-4 py-2.5 text-sm bg-surface border border-surface-border rounded-xl text-text focus:outline-none focus:border-gold/40 transition-colors appearance-none cursor-pointer"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%238a8a8a' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E")`,
              backgroundRepeat: 'no-repeat',
              backgroundPosition: 'right 16px center',
            }}
          >
            {sortOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label} ({ascending ? '↑' : '↓'})
              </option>
            ))}
          </select>
        </div>

        {/* Ascending Toggle */}
        <label className="flex items-center gap-2 cursor-pointer select-none mt-4">
          <input
            type="checkbox"
            checked={ascending}
            onChange={(e) => setAscending(e.target.checked)}
            className="w-4 h-4 rounded border-surface-border bg-surface accent-gold cursor-pointer"
          />
          <span className="text-xs text-text-muted">Ascending order</span>
        </label>
      </div>

      {/* Table Card */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="event-table w-full">
            <thead>
              <tr className="border-b border-surface-border">
                <th className="text-center font-mono text-text-muted text-[10px] w-10">#</th>
                <th className="text-left text-xs font-semibold text-text-muted">Planet</th>
                <th className="text-left text-xs font-semibold text-text-muted">Mission</th>
                <th className="text-left text-xs font-semibold text-text-muted">Class</th>
                <th className="text-right text-xs font-semibold text-text-muted">R (R⊕)</th>
                <th className="text-right text-xs font-semibold text-text-muted">Period (d)</th>
                <th className="text-right text-xs font-semibold text-text-muted">Temp (K)</th>
                <th className="text-right text-xs font-semibold text-text-muted">Insol</th>
                <th className="text-right text-xs font-semibold text-text-muted">ESI</th>
                <th className="text-left text-xs font-semibold text-text-muted pl-6">Score</th>
                <th className="text-left text-xs font-semibold text-text-muted pr-4">Tidal Lock</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((item, index) => (
                <tr
                  key={item.id}
                  className="transition-colors cursor-pointer border-b border-surface-border/40 hover:bg-white/2"
                >
                  <td className="text-center font-mono text-text-muted text-xs font-medium py-3">{index}</td>
                  <td className="font-mono text-sm text-text font-semibold py-3">{item.planet}</td>
                  <td className="text-text-muted text-xs py-3">{item.mission}</td>
                  <td className="text-text text-xs py-3">{item.sizeClass}</td>
                  <td className="font-mono text-sm text-text text-right py-3">{(item.radius || 0).toFixed(2)}</td>
                  <td className="font-mono text-sm text-text text-right py-3">{(item.period || 0).toFixed(2)}</td>
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
                  <td className="text-text-muted text-xs py-3 pr-4">{item.tidalLock}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
