import { useQuery } from '@tanstack/react-query';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { fetchMarketMovers } from '../services/api';
import { formatPrice } from '../components/common/formatPrice';

export default function TrendsPage() {
  const { data: movers, isLoading } = useQuery({ queryKey: ['market-movers'], queryFn: () => fetchMarketMovers(20) });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Market Trends</h1>

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : !movers?.length ? (
        <p className="text-sm text-slate-500">No trend data yet. Benchmarks need to be populated first.</p>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Vehicle</th>
                <th className="px-4 py-3 text-left font-medium text-slate-500">Period</th>
                <th className="px-4 py-3 text-right font-medium text-slate-500">Previous Avg</th>
                <th className="px-4 py-3 text-right font-medium text-slate-500">Current Avg</th>
                <th className="px-4 py-3 text-right font-medium text-slate-500">Change</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {movers.map((m, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-900">
                    {m.make} {m.model} {m.generation && `(${m.generation})`}
                  </td>
                  <td className="px-4 py-3 text-slate-500">{m.period}</td>
                  <td className="px-4 py-3 text-right text-slate-500">{formatPrice(m.previous_avg)}</td>
                  <td className="px-4 py-3 text-right font-semibold">{formatPrice(m.current_avg)}</td>
                  <td className="px-4 py-3 text-right">
                    <span className={`inline-flex items-center gap-1 font-semibold ${m.price_change_pct >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                      {m.price_change_pct >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                      {m.price_change_pct >= 0 ? '+' : ''}{m.price_change_pct.toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
