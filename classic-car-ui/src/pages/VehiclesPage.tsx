import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { fetchVehicles } from '../services/api';
import { formatPrice } from '../components/common/formatPrice';

export default function VehiclesPage() {
  const { data: vehicles, isLoading } = useQuery({ queryKey: ['vehicles'], queryFn: fetchVehicles });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Tracked Vehicles</h1>

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : !vehicles?.length ? (
        <p className="text-sm text-slate-500">No vehicles tracked yet.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {vehicles.map((v) => (
            <Link
              key={v.id}
              to={`/vehicles/${v.id}`}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-900">{v.make} {v.model}</p>
                  <p className="text-xs text-slate-500">
                    {v.generation && `${v.generation} · `}
                    {v.year_start}–{v.year_end ?? 'present'}
                  </p>
                </div>
                {v.price_trend !== null && (
                  <div className={`flex items-center gap-1 text-xs font-semibold ${v.price_trend >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    {v.price_trend >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {v.price_trend >= 0 ? '+' : ''}{v.price_trend?.toFixed(1)}%
                  </div>
                )}
              </div>
              <div className="mt-3 flex items-center gap-4 text-sm">
                <div>
                  <span className="text-xs text-slate-500">Avg Price</span>
                  <p className="font-semibold text-slate-900">{formatPrice(v.current_avg_price)}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-500">Listings</span>
                  <p className="font-semibold text-slate-900">{v.active_listings}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
