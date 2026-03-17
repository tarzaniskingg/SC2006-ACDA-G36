// In dev: Vite proxy rewrites /api → localhost:8000
// In prod (GitHub Pages): VITE_API_URL points to the deployed backend
const BASE = import.meta.env.VITE_API_URL || '/api';

export async function fetchRoutes(params) {
  const query = new URLSearchParams();
  query.set('origin', params.origin);
  query.set('destination', params.destination);
  if (params.departure_time) query.set('departure_time', params.departure_time);
  // Mode toggles
  if (params.include_transit != null) query.set('include_transit', params.include_transit);
  if (params.include_driving != null) query.set('include_driving', params.include_driving);
  if (params.mrt_only) query.set('mrt_only', 'true');
  if (params.public_only) query.set('public_only', 'true');
  // Weights (4-dimension: time, cost, risk, comfort)
  if (params.wt_time != null) query.set('wt_time', params.wt_time);
  if (params.wt_cost != null) query.set('wt_cost', params.wt_cost);
  if (params.wt_risk != null) query.set('wt_risk', params.wt_risk);
  if (params.wt_comfort != null) query.set('wt_comfort', params.wt_comfort);
  // Constraints
  if (params.max_walk_min != null) query.set('max_walk_min', params.max_walk_min);
  if (params.max_transfers != null) query.set('max_transfers', params.max_transfers);
  if (params.max_budget != null) query.set('max_budget', params.max_budget);

  const res = await fetch(`${BASE}/routes?${query}`);
  if (!res.ok) throw new Error(`Routes API error: ${res.status}`);
  return res.json();
}

export async function fetchDatasets() {
  const res = await fetch(`${BASE}/datasets`);
  if (!res.ok) throw new Error(`Datasets API error: ${res.status}`);
  return res.json();
}

export async function refreshCache() {
  const res = await fetch(`${BASE}/refresh`, { method: 'POST' });
  if (!res.ok) throw new Error(`Refresh API error: ${res.status}`);
  return res.json();
}

export async function fetchSettings() {
  const res = await fetch(`${BASE}/settings`);
  if (!res.ok) throw new Error(`Settings API error: ${res.status}`);
  return res.json();
}

export async function updateSettings(settings) {
  const res = await fetch(`${BASE}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error(`Settings API error: ${res.status}`);
  return res.json();
}

/**
 * Geocode a place name to [lat, lng] using Nominatim (free, no API key).
 * Appends ", Singapore" for better results in SG context.
 */
export async function geocode(placeName) {
  const query = encodeURIComponent(placeName + ', Singapore');
  const res = await fetch(
    `https://nominatim.openstreetmap.org/search?q=${query}&format=json&limit=1`,
    { headers: { 'User-Agent': 'SGTravelBud/1.0' } }
  );
  if (!res.ok) return null;
  const data = await res.json();
  if (data.length === 0) return null;
  return [parseFloat(data[0].lat), parseFloat(data[0].lon)];
}
