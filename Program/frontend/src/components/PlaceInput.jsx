import { useState, useRef, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { TILE_URL, TILE_ATTR } from './mapTiles';

const DEBOUNCE_MS = 300;
const ONEMAP_BASE = 'https://www.onemap.gov.sg/api/common/elastic/search';

const pinIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41],
});

async function onemapSearch(q) {
  const params = new URLSearchParams({
    searchVal: q, returnGeom: 'Y', getAddrDetails: 'Y', pageNum: '1',
  });
  const res = await fetch(`${ONEMAP_BASE}?${params}`);
  if (!res.ok) return [];
  const json = await res.json();
  return json.results || [];
}

function parseResults(data) {
  return data.slice(0, 5).map(item => {
    const building = item.BUILDING && item.BUILDING !== 'NIL' ? item.BUILDING : '';
    const blk = item.BLK_NO && item.BLK_NO !== 'NIL' ? item.BLK_NO : '';
    const road = item.ROAD_NAME && item.ROAD_NAME !== 'NIL' ? item.ROAD_NAME : '';
    const postal = item.POSTAL && item.POSTAL !== 'NIL' ? item.POSTAL : '';

    let title, subtitle;
    if (building) {
      title = building;
      subtitle = blk && road ? `${blk} ${road}` : road || postal;
    } else if (blk && road) {
      title = `${blk} ${road}`;
      subtitle = postal ? `S(${postal})` : '';
    } else if (road) {
      title = road;
      subtitle = postal ? `S(${postal})` : '';
    } else {
      title = item.SEARCHVAL || item.ADDRESS || '';
      subtitle = '';
    }

    const selectValue = [title, subtitle].filter(Boolean).join(', ') + ', Singapore';
    return {
      selectValue,
      title,
      subtitle,
      lat: parseFloat(item.LATITUDE),
      lon: parseFloat(item.LONGITUDE),
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
        const data = await onemapSearch(input);
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
