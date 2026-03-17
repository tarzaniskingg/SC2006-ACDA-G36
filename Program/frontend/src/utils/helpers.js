// Backend returns capitalized risk categories: "Low", "Medium", "High", "Unknown"

export function riskBadgeClass(category) {
  switch (category) {
    case 'Low': return 'bg-emerald-100 text-emerald-700';
    case 'Medium': return 'bg-amber-100 text-amber-700';
    case 'High': return 'bg-red-100 text-red-700';
    default: return 'bg-slate-100 text-slate-500';
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
