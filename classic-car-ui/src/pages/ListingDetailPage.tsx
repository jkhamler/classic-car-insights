import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ExternalLink, ArrowLeft } from 'lucide-react';
import { fetchListing, fetchComparables, fetchOpportunityReport } from '../services/api';
import ScoreBadge from '../components/common/ScoreBadge';
import { formatPrice } from '../components/common/formatPrice';

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const listingId = Number(id);

  const { data: listing, isLoading } = useQuery({ queryKey: ['listing', listingId], queryFn: () => fetchListing(listingId) });
  const { data: comparables } = useQuery({ queryKey: ['comparables', listingId], queryFn: () => fetchComparables(listingId) });
  const { data: report } = useQuery({ queryKey: ['report', listingId], queryFn: () => fetchOpportunityReport(listingId) });

  if (isLoading) return <p className="text-slate-500">Loading...</p>;
  if (!listing) return <p className="text-slate-500">Listing not found.</p>;

  const scoreDetails = listing.score_details;

  return (
    <div className="space-y-6">
      <Link to="/listings" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Back to listings
      </Link>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-start justify-between gap-4">
              <h1 className="text-xl font-bold text-slate-900">{listing.title}</h1>
              <ScoreBadge score={listing.undervaluation_score} />
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
              <div><span className="text-slate-500">Price</span><p className="font-semibold">{formatPrice(listing.price_gbp)}</p></div>
              <div><span className="text-slate-500">Year</span><p className="font-semibold">{listing.year ?? '—'}</p></div>
              <div><span className="text-slate-500">Mileage</span><p className="font-semibold">{listing.mileage ? `${listing.mileage.toLocaleString()} ${listing.mileage_unit}` : '—'}</p></div>
              <div><span className="text-slate-500">Transmission</span><p className="font-semibold">{listing.transmission ?? '—'}</p></div>
              <div><span className="text-slate-500">Color</span><p className="font-semibold">{listing.color ?? '—'}</p></div>
              <div><span className="text-slate-500">Location</span><p className="font-semibold">{listing.location ?? '—'}</p></div>
            </div>

            <a href={listing.listing_url} target="_blank" rel="noopener noreferrer"
               className="mt-4 inline-flex items-center gap-1 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700">
              View Original Listing <ExternalLink className="h-4 w-4" />
            </a>
          </div>

          {listing.description && (
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="mb-2 text-sm font-semibold text-slate-900">Description</h2>
              <p className="text-sm text-slate-600 whitespace-pre-line">{listing.description}</p>
            </div>
          )}

          {report?.content && (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-6 shadow-sm">
              <h2 className="mb-2 text-sm font-semibold text-emerald-900">AI Analysis</h2>
              <div className="prose prose-sm prose-emerald max-w-none text-emerald-800"
                   dangerouslySetInnerHTML={{ __html: report.content.replace(/\n/g, '<br/>') }} />
            </div>
          )}
        </div>

        <div className="space-y-4">
          {scoreDetails && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="mb-3 text-sm font-semibold text-slate-900">Score Breakdown</h2>
              <div className="space-y-3">
                {[
                  { label: 'Price vs Benchmark', value: scoreDetails.price_vs_benchmark },
                  { label: 'Mileage', value: scoreDetails.mileage_adjustment },
                  { label: 'Market Trend', value: scoreDetails.market_trend },
                  { label: 'Scarcity', value: scoreDetails.scarcity },
                  { label: 'Freshness', value: scoreDetails.freshness },
                  { label: 'Source Quality', value: scoreDetails.source_quality },
                ].map(({ label, value }) => (
                  <div key={label}>
                    <div className="flex justify-between text-xs text-slate-500">
                      <span>{label}</span><span>{value.toFixed(0)}/100</span>
                    </div>
                    <div className="mt-1 h-2 rounded-full bg-slate-100">
                      <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${Math.min(value, 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              {scoreDetails.explanation && (
                <p className="mt-3 text-xs text-slate-500">{scoreDetails.explanation}</p>
              )}
            </div>
          )}

          {comparables && comparables.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="mb-3 text-sm font-semibold text-slate-900">Comparable Listings</h2>
              <div className="space-y-2">
                {comparables.slice(0, 5).map((c) => (
                  <Link key={c.id} to={`/listings/${c.id}`}
                        className="block rounded-lg border border-slate-100 p-3 text-sm hover:bg-slate-50">
                    <p className="font-medium text-slate-900 line-clamp-1">{c.title}</p>
                    <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                      <span className="font-semibold text-slate-700">{formatPrice(c.price_gbp)}</span>
                      <ScoreBadge score={c.undervaluation_score} />
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
