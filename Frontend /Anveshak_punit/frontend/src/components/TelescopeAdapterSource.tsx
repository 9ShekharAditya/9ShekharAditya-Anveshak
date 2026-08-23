import { Telescope, Layers, Satellite, Radio, CheckCircle2, LucideIcon } from 'lucide-react';

export interface DatasetOption {
  id: string;
  name: string;
  icon: LucideIcon;
  totalCandidates: string;
  inHz: string;
  highPotential: string;
  earthLike: string;
}

export const DATASET_OPTIONS: DatasetOption[] = [
  {
    id: 'all',
    name: 'All Datasets Combined',
    icon: Layers,
    totalCandidates: '15,975',
    inHz: '318',
    highPotential: '48',
    earthLike: '82',
  },
  {
    id: 'kepler',
    name: 'Kepler Candidates (Cumulative)',
    icon: Telescope,
    totalCandidates: '1,977',
    inHz: '142',
    highPotential: '24',
    earthLike: '46',
  },
  {
    id: 'tess',
    name: 'TESS Candidates (TOI)',
    icon: Satellite,
    totalCandidates: '6,270',
    inHz: '77',
    highPotential: '14',
    earthLike: '18',
  },
  {
    id: 'k2',
    name: 'K2 Candidates',
    icon: Radio,
    totalCandidates: '1,374',
    inHz: '34',
    highPotential: '6',
    earthLike: '8',
  },
  {
    id: 'confirmed',
    name: 'Confirmed Planets (Composite)',
    icon: CheckCircle2,
    totalCandidates: '6,354',
    inHz: '65',
    highPotential: '12',
    earthLike: '21',
  },
];

interface TelescopeAdapterSourceProps {
  selectedDataset: string;
  onSelectDataset: (id: string) => void;
}

export default function TelescopeAdapterSource({
  selectedDataset,
  onSelectDataset,
}: TelescopeAdapterSourceProps) {
  return (
    <div className="px-4 py-4 border-b border-[#2d2417]">
      {/* Title Header */}
      <div className="flex items-center gap-2.5 mb-1.5">
        <Telescope className="w-4 h-4 text-white flex-shrink-0" />
        <h2 className="text-xs font-bold text-white tracking-wide uppercase">
          TELESCOPE ADAPTER SOURCE
        </h2>
      </div>

      {/* Sublabel */}
      <p className="text-[10px] font-medium text-[#8c857b] mb-3 tracking-widest uppercase">
        SELECT DATASET:
      </p>

      {/* Dataset Options */}
      <div className="space-y-2">
        {DATASET_OPTIONS.map((option) => {
          const isSelected = selectedDataset === option.id;
          const IconComponent = option.icon;
          return (
            <div
              key={option.id}
              onClick={() => onSelectDataset(option.id)}
              className={`flex items-center gap-3.5 px-4 py-3 rounded-2xl cursor-pointer select-none transition-all duration-200 group ${
                isSelected
                  ? 'bg-[#18140e] text-[#e5b869] font-bold border border-[#4a3b22] shadow-[0_4px_14px_rgba(0,0,0,0.4)]'
                  : 'hover:bg-white/[0.02] text-[#8c857b] hover:text-[#d1c9bd]'
              }`}
            >
              {/* Icon & Label */}
              <IconComponent className={`w-5 h-5 flex-shrink-0 ${isSelected ? 'text-[#e5b869]' : 'text-[#8c857b] group-hover:text-[#d1c9bd]'}`} />
              <span className="text-[14px] truncate leading-snug">
                {option.name}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
