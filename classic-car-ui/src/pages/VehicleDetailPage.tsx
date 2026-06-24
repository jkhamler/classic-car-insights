import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchVehiclePriceHistory, fetchInvestmentThesis } from '../services/api';
import { fetchVehicles } from '../services/api';

export default function VehicleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const vehicleId = Number(id);

  const { data: vehicles } = useQuery({ queryKey: ['vehicles'], queryFn: fetchVehicles });
  const vehicle = vehicles?.find((v) => v.id === vehicleId);

  const { data: priceHistory } = useQuery({
    queryKey: ['price-history', vehicleId],
    queryFn: () => fetchVehiclePriceHistory(vehicleId),
  });

  const { data: thesis } = useQuery({
    queryKey: ['thesis', vehicleId],
    queryFn: () => fetchInvestmentThesis(vehicleId),
  });

  return (
    <div className="space-y-6">
      <Link to="/vehicles" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Back to vehicles
      </Link>

      {vehicle && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-xl font-bold text-slate-900">{vehicle.make} {vehicle.model}</h1>
          <p className="text-sm text-slate-500">
            {vehicle.generation && `${vehicle.generation} · `}
            {vehicle.year_start}–{vehicle.year_end ?? 'present'}
          </p>
        </div>
      )}

      {priceHistory && priceHistory.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-slate-900">Price History</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={priceHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="period" tick={{ fontSize: 12 }} />
              <YAxis
                tickFormatter={(v: number) => `£${(v / 1000).toFixed(0)}k`}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                formatter={(value) => [`£${Number(value).toLocaleString()}`, 'Avg Price']}
                labelStyle={{ fontWeight: 600 }}
              />
              <Line type="monotone" dataKey="avg_price" stroke="#10b981" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {thesis?.content && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold text-slate-900">Investment Thesis</h2>
          <div className="prose prose-sm max-w-none text-slate-700"
               dangerouslySetInnerHTML={{ __html: thesis.content.replace(/\n/g, '<br/>') }} />
        </div>
      )}
    </div>
  );
}
