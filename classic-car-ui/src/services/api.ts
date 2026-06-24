import type {
  ListingSummary, ListingDetail, DashboardStats,
  VehicleSummary, PricePoint, MarketMover,
  PaginatedResponse, AlertRead, ReportRead,
} from '../types';

const API = '/api';

async function get<T>(url: string): Promise<T> {
  const res = await fetch(`${API}${url}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function post<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API}${url}`, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function del(url: string): Promise<void> {
  const res = await fetch(`${API}${url}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
}

// Dashboard
export const fetchDashboardStats = () => get<DashboardStats>('/dashboard/stats');
export const fetchTopOpportunities = (limit = 20, make?: string) => {
  const params = new URLSearchParams({ limit: String(limit) });
  if (make) params.set('make', make);
  return get<ListingSummary[]>(`/dashboard/top-opportunities?${params}`);
};

// Listings
export const fetchListings = (params: Record<string, string | number>) => {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '' && v !== null) sp.set(k, String(v));
  }
  return get<PaginatedResponse<ListingSummary>>(`/listings?${sp}`);
};
export const fetchListing = (id: number) => get<ListingDetail>(`/listings/${id}`);
export const fetchComparables = (id: number) => get<ListingSummary[]>(`/listings/${id}/comparables`);

// Vehicles
export const fetchVehicles = () => get<VehicleSummary[]>('/vehicles');
export const fetchVehiclePriceHistory = (id: number) => get<PricePoint[]>(`/vehicles/${id}/price-history`);

// Trends
export const fetchMarketMovers = (limit = 10) => get<MarketMover[]>(`/trends/movers?limit=${limit}`);

// Alerts
export const fetchAlerts = () => get<AlertRead[]>('/alerts');
export const createAlert = (data: unknown) => post<AlertRead>('/alerts', data);
export const deleteAlert = (id: number) => del(`/alerts/${id}`);

// Reports
export const fetchWeeklyDigest = () => get<ReportRead | null>('/reports/weekly');
export const fetchOpportunityReport = (listingId: number) => get<ReportRead | null>(`/reports/opportunity/${listingId}`);
export const fetchInvestmentThesis = (vehicleId: number) => get<ReportRead | null>(`/reports/investment-thesis/${vehicleId}`);
