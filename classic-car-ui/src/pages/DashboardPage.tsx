import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { TrendingUp, Car, Zap, Bell } from 'lucide-react';
import { fetchDashboardStats, fetchTopOpportunities } from '../services/api';
import ScoreBadge from '../components/common/ScoreBadge';
import { formatPrice } from '../components/common/formatPrice';

export default function DashboardPage() {
  const { data: stats } = useQuery({ queryKey: ['dashboard-stats'], queryFn: fetchDashboardStats });
  const { data: opportunities } = useQuery({ queryKey: ['top-opportunities'], queryFn: () => fetchTopOpportunities(12) });

  const statCards = [
    { label: 'Active Listings', value: stats?.total_listings ?? '—', icon: Car, color: 'text-blue-600' },
    { label: 'Vehicles Tracked', value: stats?.total_vehicles ?? '—', icon: TrendingUp, color: 'text-emerald-600' },
    { label: 'Opportunities This Week', value: stats?.opportunities_this_week ?? '—', icon: Zap, color: 'text-amber-600' },
    { label: 'Active Alerts', value: stats?.active_alerts ?? '—', icon: Bell, color: 'text-purple-600' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-500">{label}</p>
              <Icon className={`h-5 w-5 ${color}`} />
            </div>
            <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
          </div>
        ))}
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-900">Top Opportunities</h2>
        {!opportunities?.length ? (
          <p className="text-sm text-slate-500">No scored opportunities yet. Run the scrapers from the admin API to populate data.</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {opportunities.map((l) => (
              <Link
                key={l.id}
                to={`/listings/${l.id}`}
                className="group rounded-xl border border-slate-200 bg-white shadow-sm transition-shadow hover:shadow-md"
              >
                {l.image_url && (
                  <div className="h-40 overflow-hidden rounded-t-xl bg-slate-100">
                    <img src={l.image_url} alt={l.title} className="h-full w-full object-cover" />
                  </div>
                )}
                <div className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-sm font-semibold text-slate-900 group-hover:text-emerald-700 line-clamp-2">
                      {l.title}
                    </h3>
                    <ScoreBadge score={l.undervaluation_score} />
                  </div>
                  <div className="mt-2 flex items-center gap-3 text-sm text-slate-500">
                    <span className="font-semibold text-slate-900">{formatPrice(l.price_gbp)}</span>
                    {l.year && <span>{l.year}</span>}
                    {l.location && <span>{l.location}</span>}
                  </div>
                  {l.source_name && (
                    <span className="mt-2 inline-block rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                      {l.source_name}
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
