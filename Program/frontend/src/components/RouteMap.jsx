import { MapContainer, TileLayer, Polyline, Marker, Popup, Tooltip, useMap, CircleMarker } from 'react-leaflet';
import React, { useEffect, useState, useMemo } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { stepColor, modeColor, decodePolyline, formatDuration } from '../utils/helpers';
import { geocode } from '../utils/api';
import { TILE_URL, TILE_ATTR } from './mapTiles';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const SG_CENTER = [1.3521, 103.8198];

function makeIcon(color) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 36" width="28" height="42">
    <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24s12-15 12-24C24 5.4 18.6 0 12 0z" fill="${color}" stroke="#fff" stroke-width="1.5"/>
    <circle cx="12" cy="12" r="5" fill="#fff"/>
  </svg>`;
  return new L.Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(svg)}`,
    iconSize: [28, 42], iconAnchor: [14, 42], popupAnchor: [0, -42],
  });
}

const startIcon = makeIcon('#22c55e');
const endIcon = makeIcon('#ef4444');

function makeLabelIcon(text, bgColor) {
  const html = `<div style="
    background:${bgColor}; color:#fff; font-size:11px; font-weight:600;
    padding:2px 8px; border-radius:10px; white-space:nowrap;
    border:2px solid #fff; box-shadow:0 1px 4px rgba(0,0,0,0.2);
    font-family:-apple-system,sans-serif;
  ">${text}</div>`;
  return L.divIcon({ html, className: '', iconSize: null, iconAnchor: [0, 12] });
}

function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds?.length >= 2) map.fitBounds(bounds, { padding: [50, 50] });
  }, [bounds, map]);
  return null;
}

function InvalidateSize() {
  const map = useMap();
  useEffect(() => {
    const t = setTimeout(() => map.invalidateSize(), 100);
    return () => clearTimeout(t);
  }, [map]);
  return null;
}

/**
 * Split a polyline into N segments proportional to step distances.
 * Returns array of { positions, step } for each step.
 */
function splitPolylineBySteps(points, steps) {
  if (!points.length || !steps.length) return [];

  const totalDist = steps.reduce((s, st) => s + (st.distance_m || 0), 0);
  if (totalDist === 0) {
    // Equal split fallback
    const chunkSize = Math.max(1, Math.floor(points.length / steps.length));
    return steps.map((step, i) => ({
      positions: points.slice(i * chunkSize, i === steps.length - 1 ? points.length : (i + 1) * chunkSize + 1),
      step,
    })).filter(s => s.positions.length >= 2);
  }

  const segments = [];
  let ptIdx = 0;

  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const frac = (step.distance_m || 0) / totalDist;
    const numPts = Math.max(1, Math.round(frac * (points.length - 1)));
    const endIdx = i === steps.length - 1
      ? points.length - 1
      : Math.min(ptIdx + numPts, points.length - 1);

    const slice = points.slice(ptIdx, endIdx + 1);
    if (slice.length >= 2) {
      segments.push({ positions: slice, step });
    }
    ptIdx = endIdx;
  }

  return segments;
}

export default function RouteMap({ route, query }) {
  const [geoMarkers, setGeoMarkers] = useState({ start: null, end: null });

  const polylinePoints = useMemo(() => {
    if (route?.overview_polyline) return decodePolyline(route.overview_polyline);
    return [];
  }, [route?.overview_polyline]);

  useEffect(() => {
    if (!query) return;
    let cancelled = false;
    (async () => {
      const [s, e] = await Promise.all([geocode(query.origin), geocode(query.destination)]);
      if (!cancelled) setGeoMarkers({ start: s, end: e });
    })();
    return () => { cancelled = true; };
  }, [query?.origin, query?.destination]);

  const hasPolyline = polylinePoints.length > 0;
  const fallbackLine = (!hasPolyline && geoMarkers.start && geoMarkers.end)
    ? [geoMarkers.start, geoMarkers.end] : [];

  const startMarker = hasPolyline ? polylinePoints[0] : geoMarkers.start;
  const endMarker = hasPolyline ? polylinePoints[polylinePoints.length - 1] : geoMarkers.end;

  const boundsPoints = [];
  if (startMarker) boundsPoints.push(startMarker);
  if (endMarker) boundsPoints.push(endMarker);
  if (hasPolyline) boundsPoints.push(...polylinePoints);

  // Split the polyline into per-step colored segments
  const coloredSegments = useMemo(() => {
    if (!hasPolyline || !route?.steps?.length) return [];
    return splitPolylineBySteps(polylinePoints, route.steps);
  }, [hasPolyline, polylinePoints, route?.steps]);

  // Build step labels
  const stepLabels = useMemo(() => {
    if (!coloredSegments.length) return [];
    return coloredSegments.map((seg, i) => {
      const step = seg.step;
      // Place label at the midpoint of the segment
      const midIdx = Math.floor(seg.positions.length / 2);
      const pos = seg.positions[midIdx];
      let text = step.mode;
      if (step.line_name) text = `${step.mode} ${step.line_name}`;
      if (step.mode === 'Walk') text = `Walk ${formatDuration(step.duration_min)}`;
      const steps = route.steps;
      return {
        pos, text, step,
        isTransfer: i > 0 && steps[i - 1].mode !== 'Walk' && step.mode !== 'Walk',
      };
    });
  }, [coloredSegments, route?.steps]);

  const hasModeSegments = coloredSegments.length > 0;
  const fallbackColor = route?.category?.includes('Taxi') || route?.category?.includes('Drive')
    ? modeColor('Drive') : modeColor('Train');

  return (
    <MapContainer center={startMarker || SG_CENTER} zoom={13}
      style={{ width: '100%', height: '100%' }} zoomControl={false}>
      <TileLayer attribution={TILE_ATTR} url={TILE_URL} />
      <InvalidateSize />
      {boundsPoints.length >= 2 && <FitBounds bounds={boundsPoints} />}

      {/* Per-step colored polylines */}
      {hasModeSegments && coloredSegments.map((seg, i) => {
        const color = stepColor(seg.step);
        const isWalk = seg.step.mode === 'Walk';
        return (
          <React.Fragment key={`seg-${i}`}>
            <Polyline positions={seg.positions}
              pathOptions={{ color: '#fff', weight: isWalk ? 6 : 8, opacity: 0.9 }} />
            <Polyline positions={seg.positions}
              pathOptions={{
                color,
                weight: isWalk ? 4 : 6,
                opacity: 0.9,
                dashArray: isWalk ? '8, 8' : undefined,
              }} />
          </React.Fragment>
        );
      })}

      {/* Fallback: single-color polyline when no step segments */}
      {!hasModeSegments && hasPolyline && (
        <>
          <Polyline positions={polylinePoints}
            pathOptions={{ color: '#fff', weight: 8, opacity: 0.9 }} />
          <Polyline positions={polylinePoints}
            pathOptions={{ color: fallbackColor, weight: 5, opacity: 0.9 }} />
        </>
      )}

      {/* Fallback: dashed line between geocoded points */}
      {!hasPolyline && fallbackLine.length >= 2 && (
        <>
          <Polyline positions={fallbackLine}
            pathOptions={{ color: '#fff', weight: 8, opacity: 0.9 }} />
          <Polyline positions={fallbackLine}
            pathOptions={{ color: fallbackColor, weight: 5, opacity: 0.9, dashArray: '10, 10' }} />
        </>
      )}

      {/* Step labels */}
      {stepLabels.map((sl, i) => (
        <Marker key={`label-${i}`} position={sl.pos}
          icon={makeLabelIcon(sl.text, stepColor(sl.step))} interactive>
          <Popup>
            <div style={{ fontSize: '12px', lineHeight: '1.4' }}>
              <strong>{sl.text}</strong>
              {sl.step.from_name && sl.step.to_name && (
                <div>{sl.step.from_name} → {sl.step.to_name}</div>
              )}
              {sl.step.duration_min && <div>{formatDuration(sl.step.duration_min)}</div>}
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Transfer dots */}
      {stepLabels.filter(sl => sl.isTransfer).map((sl, i) => (
        <CircleMarker key={`xfer-${i}`} center={sl.pos} radius={7}
          pathOptions={{ color: '#fff', weight: 3, fillColor: '#f59e0b', fillOpacity: 1 }}>
          <Tooltip direction="top" offset={[0, -10]}>
            Transfer at {sl.step.from_name}
          </Tooltip>
        </CircleMarker>
      ))}

      {/* Start / End markers */}
      {startMarker && (
        <Marker position={startMarker} icon={startIcon}>
          <Popup><strong>Start</strong><br />{query?.origin}</Popup>
        </Marker>
      )}
      {endMarker && (
        <Marker position={endMarker} icon={endIcon}>
          <Popup><strong>End</strong><br />{query?.destination}</Popup>
        </Marker>
      )}
    </MapContainer>
  );
}
