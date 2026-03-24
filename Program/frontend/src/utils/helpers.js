// Backend returns capitalized risk categories: "Low", "Medium", "High", "Unknown"

export function riskBadgeClass(category) {
  switch (category) {
    case 'Low': return 'bg-emerald-500/15 text-emerald-400 ring-emerald-500/20';
    case 'Medium': return 'bg-amber-500/15 text-amber-400 ring-amber-500/20';
    case 'High': return 'bg-red-500/15 text-red-400 ring-red-500/20';
    default: return 'bg-white/5 text-slate-400 ring-white/10';
  }
}

export function riskLabel(category) {
  if (!category || category === 'Unknown') return 'N/A';
  return category;
}

export function modeColor(mode) {
  switch (mode) {
    case 'Walk': return '#64748b';
    case 'Bus': return '#22c55e';
    case 'Train': return '#3b82f6';
    case 'Drive': return '#f59e0b';
    case 'Tram': return '#8b5cf6';
    case 'Ferry': return '#06b6d4';
    default: return '#94a3b8';
  }
}

// Official SG MRT line colours
const MRT_LINE_COLORS = {
  'EW': '#009645', 'CG': '#009645',  // East-West — green
  'NS': '#D42E12',                     // North-South — red
  'NE': '#9900AA',                     // North-East — purple
  'CC': '#FA9E0D', 'CE': '#FA9E0D',  // Circle — orange
  'DT': '#005EC4',                     // Downtown — blue
  'TE': '#9D5B25',                     // Thomson-East Coast — brown
  'BP': '#748477', 'SW': '#748477', 'SE': '#748477', 'PW': '#748477', 'PE': '#748477', // LRT — grey
};

export function stepColor(step) {
  if (!step) return '#94a3b8';
  const mode = step.mode;
  if (mode === 'Walk') return '#64748b';
  if (mode === 'Drive') return '#f59e0b';
  if (mode === 'Bus') return '#22c55e';
  if (mode === 'Ferry') return '#06b6d4';
  // For trains, match the MRT line code
  if (mode === 'Train' && step.line_name) {
    const code = step.line_name.replace(/[0-9]/g, '').toUpperCase();
    if (MRT_LINE_COLORS[code]) return MRT_LINE_COLORS[code];
  }
  return modeColor(mode);
}

export function formatDuration(minutes) {
  if (minutes == null) return '--';
  const m = Math.round(minutes);
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  const rem = m % 60;
  return rem > 0 ? `${h}h ${rem}m` : `${h}h`;
}

export function formatCost(cost) {
  if (cost == null) return '--';
  return `$${cost.toFixed(2)}`;
}

// Bus frequency risk color (Feature 5)
export function frequencyBadgeClass(cat) {
  switch (cat) {
    case 'High': return 'bg-emerald-500/15 text-emerald-400 ring-emerald-500/20';
    case 'Medium': return 'bg-amber-500/15 text-amber-400 ring-amber-500/20';
    case 'Low': return 'bg-red-500/15 text-red-400 ring-red-500/20';
    default: return 'bg-white/5 text-slate-400 ring-white/10';
  }
}

export function frequencyLabel(freq) {
  if (!freq) return null;
  const min = freq.frequency_min;
  if (min <= 8) return `Every ${min} min`;
  if (min <= 15) return `Every ${min} min`;
  return `Every ${min} min`;
}

// Weather helpers (Feature 2)
export function isRainy(weather) {
  return weather?.rain === true;
}

// Crowding heatmap color (Feature 4)
export function crowdColor(level) {
  switch (level) {
    case 'Low': return '#10b981';     // emerald
    case 'Medium': return '#f59e0b';  // amber
    case 'High': return '#ef4444';    // red
    default: return '#94a3b8';        // slate
  }
}

export function decodePolyline(encoded) {
  if (!encoded) return [];
  const points = [];
  let index = 0, lat = 0, lng = 0;
  while (index < encoded.length) {
    let b, shift = 0, result = 0;
    do { b = encoded.charCodeAt(index++) - 63; result |= (b & 0x1f) << shift; shift += 5; } while (b >= 0x20);
    lat += (result & 1) ? ~(result >> 1) : (result >> 1);
    shift = 0; result = 0;
    do { b = encoded.charCodeAt(index++) - 63; result |= (b & 0x1f) << shift; shift += 5; } while (b >= 0x20);
    lng += (result & 1) ? ~(result >> 1) : (result >> 1);
    points.push([lat / 1e5, lng / 1e5]);
  }
  return points;
}
