export interface ListingSummary {
  id: number;
  title: string;
  listing_url: string;
  make: string | null;
  model: string | null;
  year: number | null;
  asking_price: number | null;
  price_gbp: number | null;
  currency: string;
  location: string | null;
  source_name: string | null;
  undervaluation_score: number | null;
  status: string;
  scraped_at: string | null;
  image_url: string | null;
}

export interface ListingDetail {
  id: number;
  vehicle_id: number | null;
  source_id: number;
  external_id: string;
  title: string;
  listing_url: string;
  listing_type: string;
  status: string;
  asking_price: number | null;
  sale_price: number | null;
  currency: string;
  price_gbp: number | null;
  make: string | null;
  model: string | null;
  year: number | null;
  mileage: number | null;
  mileage_unit: string;
  vin: string | null;
  color: string | null;
  transmission: string | null;
  location: string | null;
  description: string | null;
  image_urls: string[] | null;
  listed_at: string | null;
  scraped_at: string | null;
  undervaluation_score: number | null;
  score_details: ScoreBreakdown | null;
}

export interface ScoreBreakdown {
  price_vs_benchmark: number;
  mileage_adjustment: number;
  market_trend: number;
  scarcity: number;
  freshness: number;
  source_quality: number;
  total: number;
  explanation: string;
}

export interface DashboardStats {
  total_listings: number;
  total_vehicles: number;
  opportunities_this_week: number;
  active_alerts: number;
}

export interface VehicleSummary {
  id: number;
  make: string;
  model: string;
  generation: string | null;
  year_start: number | null;
  year_end: number | null;
  current_avg_price: number | null;
  price_trend: number | null;
  active_listings: number;
}

export interface PricePoint {
  period: string;
  avg_price: number;
  sample_count: number;
  price_trend: number | null;
}

export interface MarketMover {
  vehicle_id: number;
  make: string;
  model: string;
  generation: string | null;
  price_change_pct: number;
  current_avg: number;
  previous_avg: number;
  period: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}

export interface AlertRead {
  id: number;
  name: string;
  alert_type: string;
  criteria_json: Record<string, unknown>;
  is_active: boolean;
  notification_channel: string;
  last_triggered_at: string | null;
  created_at: string | null;
}

export interface ReportRead {
  id: number;
  report_type: string;
  title: string | null;
  content: string;
  generated_at: string;
}
