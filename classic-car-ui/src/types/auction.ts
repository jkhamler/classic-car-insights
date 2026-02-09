export interface PriceTrendPoint {
  period: string;
  avg_price: number;
  min_price: number;
  max_price: number;
  count: number;
}

export interface PriceTrendSeries {
  make: string;
  data: PriceTrendPoint[];
  avg_price: number;
  total_count: number;
}

export interface PriceTrendResponse {
  series: PriceTrendSeries[];
}

export interface FilterOptions {
  makes: string[];
  models: string[];
  years: number[];
}

export interface ImportResponse {
  imported: number;
  make: string;
  model: string | null;
}
