import type { PriceTrendResponse, FilterOptions, ImportResponse } from '../types/auction';

const BASE = '/api/auction-sales';

export async function fetchPriceTrends(params: {
  makes?: string[];
  model?: string;
  year_min?: number;
  year_max?: number;
}): Promise<PriceTrendResponse> {
  const url = new URL(`${BASE}/trends`, window.location.origin);
  if (params.makes) {
    for (const m of params.makes) {
      url.searchParams.append('make', m);
    }
  }
  if (params.model) url.searchParams.set('model', params.model);
  if (params.year_min != null) url.searchParams.set('year_min', String(params.year_min));
  if (params.year_max != null) url.searchParams.set('year_max', String(params.year_max));

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Failed to fetch trends: ${res.status}`);
  return res.json();
}

export async function fetchFilterOptions(): Promise<FilterOptions> {
  const res = await fetch(`${BASE}/filters`);
  if (!res.ok) throw new Error(`Failed to fetch filters: ${res.status}`);
  return res.json();
}

export async function triggerImport(
  make: string,
  model?: string,
  limit: number = 50,
): Promise<ImportResponse> {
  const url = new URL(`${BASE}/import`, window.location.origin);
  url.searchParams.set('make', make);
  if (model) url.searchParams.set('model', model);
  url.searchParams.set('limit', String(limit));

  const res = await fetch(url.toString(), { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to import: ${res.status}`);
  return res.json();
}
