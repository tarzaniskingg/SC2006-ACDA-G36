import { useState, useRef, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { TILE_URL, TILE_ATTR } from './mapTiles';

const DEBOUNCE_MS = 300;
const NOM_BASE = 'https://nominatim.openstreetmap.org/search';
const NOM_OPTS = { headers: { 'User-Agent': 'SGTravelBud/1.0' } };
const SG_CENTER = [1.3521, 103.8198];

const pinIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41],
});

async function nominatimSearch(q) {
  const params = new URLSearchParams({
    q, format: 'json', limit: '5', countrycodes: 'sg', addressdetails: '1',
  });
  const res = await fetch(`${NOM_BASE}?${params}`, NOM_OPTS);
  return res.ok ? res.json() : [];
}

function parseResults(data) {
  return data.map(item => {
    const addr = item.address || {};
    const parts = [];
    const road = addr.road || addr.pedestrian || addr.footway || '';
    const poiName = item.name || '';
    const isNameUseful = poiName && poiName !== road && !/^\d+$/.test(poiName);
    if (isNameUseful) {
      parts.push(poiName);
      if (road) parts.push(road);
    } else if (addr.house_number && road) {
      parts.push(`${addr.house_number} ${road}`);
    } else if (road) {
      parts.push(road);
    }
    const area = addr.suburb || addr.neighbourhood || addr.quarter || addr.residential || '';
    if (area && !parts.includes(area)) parts.push(area);
    if (parts.length === 0) {
      parts.push(...item.display_name.split(',').slice(0, 2).map(s => s.trim()));
    }
    const selectValue = parts.join(', ') + ', Singapore';
    return {
      selectValue,
      title: parts[0] || item.name || '',
      subtitle: parts.slice(1).join(', '),
      lat: parseFloat(item.lat),
      lon: parseFloat(item.lon),
    };
  });
}

function FlyTo({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.flyTo(center, 16, { duration: 0.8 });
  }, [center, map]);
  return null;
}

function MiniMap({ lat, lon }) {
  if (!lat || !lon) return null;
  const pos = [lat, lon];
  return (
    <div className="h-32 rounded-xl overflow-hidden border border-white/[0.08] mt-2">
      <MapContainer center={pos} zoom={16} style={{ width: '100%', height: '100%' }}
        zoomControl={false} dragging={false} scrollWheelZoom={false}
        doubleClickZoom={false} attributionControl={false}>
        <TileLayer url={TILE_URL} attribution={TILE_ATTR} />
        <FlyTo center={pos} />
        <Marker position={pos} icon={pinIcon} />
      </MapContainer>
    </div>
  );
}

export default function PlaceInput({ value, onChange, onLocationSelect, placeholder, dotColor }) {
  const [suggestions, setSuggestions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedLoc, setSelectedLoc] = useState(null);
  const timerRef = useRef(null);
  const wrapperRef = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  function handleChange(e) {
    const val = e.target.value;
    onChange(val);
    setSelectedLoc(null);

    clearTimeout(timerRef.current);
    if (val.trim().length < 2) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    timerRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const input = val.trim();
        let data = await nominatimSearch(input);
        if (data.length === 0 && input.includes(' ')) {
          const words = input.split(/\s+/);
          data = await nominatimSearch([...words].reverse().join(' '));
        }
        if (data.length === 0 && input.includes(' ')) {
          const words = input.split(/\s+/);
          for (let drop = words.length - 1; drop >= 1; drop--) {
            data = await nominatimSearch(words.filter((_, i) => i !== drop).join(' '));
            if (data.length > 0) break;
          }
        }
        const results = parseResults(data);
        setSuggestions(results);
        setShowDropdown(results.length > 0);
      } catch { /* silent */ }
      setLoading(false);
    }, DEBOUNCE_MS);
  }

  function selectSuggestion(s) {
    onChange(s.selectValue);
    setSelectedLoc({ lat: s.lat, lon: s.lon });
    onLocationSelect?.({ lat: s.lat, lon: s.lon });
    setSuggestions([]);
    setShowDropdown(false);
  }

  return (
    <div ref={wrapperRef} className="relative">
      <div className={`absolute left-3 top-[18px] -translate-y-1/2 w-2.5 h-2.5 rounded-full ${dotColor}`} />
      <input
        type="text"
        value={value}
        onChange={handleChange}
        onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
        placeholder={placeholder}
        autoComplete="off"
        className="input-dark w-full pl-9 pr-4 py-3 rounded-xl text-sm"
      />
      {loading && (
        <div className="absolute right-3 top-[18px] -translate-y-1/2">
          <div className="w-4 h-4 border-2 border-slate-600 border-t-amber-400 rounded-full animate-spin" />
        </div>
      )}
      {showDropdown && suggestions.length > 0 && (
        <div className="absolute z-50 left-0 right-0 top-full mt-1 rounded-xl overflow-hidden max-h-52 overflow-y-auto border border-white/[0.1]"
          style={{ background: 'rgba(15, 23, 42, 0.95)', backdropFilter: 'blur(16px)' }}>
          {suggestions.map((s, i) => (
            <button
              key={i}
              type="button"
              onClick={() => selectSuggestion(s)}
              className="w-full text-left px-4 py-2.5 text-sm text-slate-200 hover:bg-white/[0.06] transition-colors border-b border-white/[0.04] last:border-0"
            >
              <span className="font-medium">{s.title}</span>
              {s.subtitle && (
                <span className="text-[11px] text-slate-500 block truncate">{s.subtitle}</span>
              )}
            </button>
          ))}
        </div>
      )}
      {/* Mini preview map after selecting a place */}
      <MiniMap lat={selectedLoc?.lat} lon={selectedLoc?.lon} />
    </div>
  );
}
