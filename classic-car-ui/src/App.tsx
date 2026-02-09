import { useState, useEffect, useCallback } from 'react';
import FilterPanel from './components/FilterPanel';
import PriceTrendChart from './components/PriceTrendChart';
import { fetchPriceTrends } from './services/api';
import type { PriceTrendResponse } from './types/auction';
import './App.css';

function App() {
  const [selectedMakes, setSelectedMakes] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | undefined>();
  const [yearMin, setYearMin] = useState<number | undefined>();
  const [yearMax, setYearMax] = useState<number | undefined>();
  const [trendData, setTrendData] = useState<PriceTrendResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const loadTrends = useCallback(async () => {
    if (selectedMakes.length === 0) {
      setTrendData(null);
      return;
    }
    setLoading(true);
    try {
      const data = await fetchPriceTrends({
        makes: selectedMakes,
        model: selectedModel,
        year_min: yearMin,
        year_max: yearMax,
      });
      setTrendData(data);
    } catch (err) {
      console.error('Failed to load trends:', err);
      setTrendData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedMakes, selectedModel, yearMin, yearMax]);

  useEffect(() => {
    loadTrends();
  }, [loadTrends]);

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Classic Car Insights</h1>
          <p className="text-sm text-gray-500">Auction price trends and analytics</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        <FilterPanel
          selectedMakes={selectedMakes}
          selectedModel={selectedModel}
          yearMin={yearMin}
          yearMax={yearMax}
          onMakesChange={setSelectedMakes}
          onModelChange={setSelectedModel}
          onYearMinChange={setYearMin}
          onYearMaxChange={setYearMax}
        />

        <PriceTrendChart data={trendData} loading={loading} />
      </main>
    </div>
  );
}

export default App;
