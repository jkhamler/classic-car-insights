import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ExternalLink } from 'lucide-react';
import { fetchListings } from '../services/api';
import ScoreBadge from '../components/common/ScoreBadge';
import { formatPrice } from '../components/common/formatPrice';

export default function ListingsPage() {
  const [make, setMake] = useState('');
  const [model, setModel] = useState('');
  const [minScore, setMinScore] = useState('');
  const [sortBy, setSortBy] = useState('score');
  const [page, setPage] = useState(1);

  const params: Record<string, string | number> = { sort_by: sortBy, page, per_page: 25 };
  if (make) params.make = make;
  if (model) params.model = model;
  if (minScore) params.min_score = minScore;

  const { data, isLoading } = useQuery({
    queryKey: ['listings', params],
    queryFn: () => fetchListings(params),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Listings</h1>

      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Make</label>
          <input
            value={make} onChange={(e) => { setMake(e.target.value); setPage(1); }}
            placeholder="e.g. Porsche"
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Model</label>
          <input
            value={model} onChange={(e) => { setModel(e.target.value); setPage(1); }}
            placeholder="e.g. 911"
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Min Score</label>
          <input
            type="number" value={minScore}
            onChange={(e) => { setMinScore(e.target.value); setPage(1); }}
            placeholder="0"
            className="w-20 rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Sort</label>
          <select
            value={sortBy} onChange={(e) => setSortBy(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-emerald-500 focus:outline-none"
          >
            <option value="score">Score</option>
            <option value="price_asc">Price (Low)</option>
            <option value="price_desc">Price (High)</option>
            <option value="date">Newest</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : !data?.items.length ? (
        <p className="text-sm text-slate-500">No listings found.</p>
      ) : (
        <>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-200 bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Vehicle</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Price</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Year</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Source</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <a href={l.listing_url} target="_blank" rel="noopener noreferrer"
                         className="inline-flex items-center gap-1 font-medium text-slate-900 hover:text-emerald-700">
                        {l.title.length > 60 ? l.title.slice(0, 60) + '...' : l.title}
                        <ExternalLink className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                      </a>
                    </td>
                    <td className="px-4 py-3 font-semibold">{formatPrice(l.price_gbp)}</td>
                    <td className="px-4 py-3 text-slate-500">{l.year ?? '—'}</td>
                    <td className="px-4 py-3">
                      <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                        {l.source_name ?? '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3"><ScoreBadge score={l.undervaluation_score} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-500">{data.total} results</span>
            <div className="flex gap-2">
              <button
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                className="rounded-lg border border-slate-300 px-3 py-1 disabled:opacity-50"
              >Prev</button>
              <span className="px-2 py-1 text-slate-500">Page {page}</span>
              <button
                disabled={!data.has_next}
                onClick={() => setPage(page + 1)}
                className="rounded-lg border border-slate-300 px-3 py-1 disabled:opacity-50"
              >Next</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
