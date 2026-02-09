import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { PriceTrendResponse } from '../types/auction';

const COLORS = ['#2563eb', '#dc2626', '#16a34a', '#d97706', '#7c3aed', '#0891b2', '#be185d', '#65a30d'];

const formatUSD = (value: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);

interface PriceTrendChartProps {
  data: PriceTrendResponse | null;
  loading: boolean;
}

export default function PriceTrendChart({ data, loading }: PriceTrendChartProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
        Loading chart data...
      </div>
    );
  }

  if (!data || data.series.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
        <p className="text-lg font-medium">No trend data available</p>
        <p className="mt-1 text-sm">Select one or more makes above, or import data first.</p>
      </div>
    );
  }

  // Build merged data points: each period gets one object with keys per make
  const periodMap = new Map<string, Record<string, number | string>>();
  for (const series of data.series) {
    for (const pt of series.data) {
      if (!periodMap.has(pt.period)) {
        periodMap.set(pt.period, { period: pt.period });
      }
      periodMap.get(pt.period)![series.make] = pt.avg_price;
    }
  }
  const chartData = Array.from(periodMap.values()).sort((a, b) =>
    (a.period as string).localeCompare(b.period as string),
  );

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg shadow p-4">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" tick={{ fontSize: 12 }} />
            <YAxis tickFormatter={(v: number) => formatUSD(v)} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value) => formatUSD(Number(value))} />
            <Legend />
            {data.series.map((s, i) => (
              <Line
                key={s.make}
                type="monotone"
                dataKey={s.make}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {data.series.map((s, i) => (
          <div
            key={s.make}
            className="bg-white rounded-lg shadow p-4 border-l-4"
            style={{ borderLeftColor: COLORS[i % COLORS.length] }}
          >
            <div className="font-semibold text-gray-800">{s.make}</div>
            <div className="text-sm text-gray-500 mt-1">
              Avg Price: <span className="font-medium text-gray-700">{formatUSD(s.avg_price)}</span>
            </div>
            <div className="text-sm text-gray-500">
              Sales: <span className="font-medium text-gray-700">{s.total_count.toLocaleString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
