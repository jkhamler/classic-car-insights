import type {
  ListingSummary, ListingDetail, DashboardStats,
  VehicleSummary, PricePoint, MarketMover,
  PaginatedResponse, AlertRead, ReportRead,
  SharedVehicle, CoOwner, VehicleOwner, Booking, Expense, VehicleBalance,
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
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `API error: ${res.status}`);
  }
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

// Timeshare
export const fetchSharedVehicles = () => get<SharedVehicle[]>('/timeshare/vehicles');
export const createSharedVehicle = (data: Partial<SharedVehicle>) => post<SharedVehicle>('/timeshare/vehicles', data);

export const fetchCoOwners = () => get<CoOwner[]>('/timeshare/co-owners');
export const createCoOwner = (data: Partial<CoOwner>) => post<CoOwner>('/timeshare/co-owners', data);

export const fetchVehicleOwners = (vehicleId: number) => get<VehicleOwner[]>(`/timeshare/vehicles/${vehicleId}/owners`);
export const linkOwnerToVehicle = (vehicleId: number, coOwnerId: number) =>
  post<VehicleOwner>(`/timeshare/vehicles/${vehicleId}/owners`, { co_owner_id: coOwnerId });

export const fetchBookings = (vehicleId: number) => get<Booking[]>(`/timeshare/vehicles/${vehicleId}/bookings`);
export const createBooking = (vehicleId: number, data: Partial<Booking>) =>
  post<Booking>(`/timeshare/vehicles/${vehicleId}/bookings`, data);
export const deleteBooking = (bookingId: number) => del(`/timeshare/bookings/${bookingId}`);

export const fetchExpenses = (vehicleId: number) => get<Expense[]>(`/timeshare/vehicles/${vehicleId}/expenses`);
export const createExpense = (vehicleId: number, data: Partial<Expense>) =>
  post<Expense>(`/timeshare/vehicles/${vehicleId}/expenses`, data);
export const deleteExpense = (expenseId: number) => del(`/timeshare/expenses/${expenseId}`);

export const fetchVehicleBalance = (vehicleId: number) => get<VehicleBalance>(`/timeshare/vehicles/${vehicleId}/balance`);
