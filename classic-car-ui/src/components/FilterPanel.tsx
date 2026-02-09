import { useEffect, useState } from 'react';
import { fetchFilterOptions } from '../services/api';
import type { FilterOptions } from '../types/auction';

interface FilterPanelProps {
  selectedMakes: string[];
  selectedModel: string | undefined;
  yearMin: number | undefined;
  yearMax: number | undefined;
  onMakesChange: (makes: string[]) => void;
  onModelChange: (model: string | undefined) => void;
  onYearMinChange: (year: number | undefined) => void;
  onYearMaxChange: (year: number | undefined) => void;
}

export default function FilterPanel({
  selectedMakes,
  selectedModel,
  yearMin,
  yearMax,
  onMakesChange,
  onModelChange,
  onYearMinChange,
  onYearMaxChange,
}: FilterPanelProps) {
  const [options, setOptions] = useState<FilterOptions>({ makes: [], models: [], years: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFilterOptions()
      .then(setOptions)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const toggleMake = (make: string) => {
    if (selectedMakes.includes(make)) {
      onMakesChange(selectedMakes.filter((m) => m !== make));
    } else {
      onMakesChange([...selectedMakes, make]);
    }
  };

  if (loading) {
    return <div className="text-gray-500 text-sm">Loading filters...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-4 space-y-4">
      {/* Makes */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-2">Makes</label>
        <div className="flex flex-wrap gap-2">
          {options.makes.length === 0 && (
            <span className="text-gray-400 text-sm">No makes available. Import data first.</span>
          )}
          {options.makes.map((make) => (
            <button
              key={make}
              onClick={() => toggleMake(make)}
              className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${
                selectedMakes.includes(make)
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
              }`}
            >
              {make}
            </button>
          ))}
        </div>
      </div>

      {/* Model */}
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-1">Model</label>
        <select
          value={selectedModel ?? ''}
          onChange={(e) => onModelChange(e.target.value || undefined)}
          className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm bg-white"
        >
          <option value="">All Models</option>
          {options.models.map((model) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
      </div>

      {/* Year range */}
      <div className="flex gap-4">
        <div className="flex-1">
          <label className="block text-sm font-semibold text-gray-700 mb-1">Year From</label>
          <select
            value={yearMin ?? ''}
            onChange={(e) => onYearMinChange(e.target.value ? Number(e.target.value) : undefined)}
            className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm bg-white"
          >
            <option value="">Any</option>
            {options.years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <label className="block text-sm font-semibold text-gray-700 mb-1">Year To</label>
          <select
            value={yearMax ?? ''}
            onChange={(e) => onYearMaxChange(e.target.value ? Number(e.target.value) : undefined)}
            className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm bg-white"
          >
            <option value="">Any</option>
            {options.years.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
