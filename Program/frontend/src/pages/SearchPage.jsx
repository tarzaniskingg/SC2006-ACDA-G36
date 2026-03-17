import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, MapPin, Bus, Car, SlidersHorizontal, Loader2, AlertCircle, Footprints, ArrowLeftRight } from 'lucide-react';
import { fetchRoutes } from '../utils/api';
import PlaceInput from '../components/PlaceInput';

const POPULAR_PLACES = [
  'Changi Airport', 'Orchard Road', 'Marina Bay Sands', 'Sentosa',
  'NTU', 'NUS', 'Jurong East', 'Tampines Mall', 'Woodlands', 'Punggol',
];

export default function SearchPage({ onResults }) {
  const navigate = useNavigate();
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [modes, setModes] = useState({ transit: true, driving: true });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [weights, setWeights] = useState({ time: 0.25, cost: 0.25, risk: 0.25, comfort: 0.25 });
  const [constraints, setConstraints] = useState({ max_walk_min: '', max_transfers: '', max_budget: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function toggleMode(key) {
    setModes(prev => {
      const next = { ...prev, [key]: !prev[key] };
      if (!next.transit && !next.driving) return prev;
      return next;
    });
  }

  const modeButtons = [
    { key: 'transit', label: 'Public Transit', icon: Bus, sub: 'Bus + MRT' },
    { key: 'driving', label: 'Taxi / Drive', icon: Car, sub: 'Private car' },
  ];

  const originValid = origin.trim().length >= 2;
  const destValid = destination.trim().length >= 2;
  const samePlace = originValid && destValid && origin.trim().toLowerCase() === destination.trim().toLowerCase();
  const canSearch = originValid && destValid && !samePlace && !loading;

  async function handleSearch(e) {
    e.preventDefault();
    if (!canSearch) return;
    setLoading(true);
    setError(null);
    try {
      const params = {
        origin: origin.trim(),
        destination: destination.trim(),
        include_transit: modes.transit,
        include_driving: modes.driving,
        wt_time: weights.time,
        wt_cost: weights.cost,
        wt_risk: weights.risk,
        wt_comfort: weights.comfort,
      };
      if (constraints.max_walk_min) params.max_walk_min = parseInt(constraints.max_walk_min);
      if (constraints.max_transfers) params.max_transfers = parseInt(constraints.max_transfers);
      if (constraints.max_budget) params.max_budget = parseFloat(constraints.max_budget);
      const data = await fetchRoutes(params);
      if (!data.routes || data.routes.length === 0) {
        setError(data.message || 'No routes found. Try different locations or relax constraints.');
        return;
      }
      onResults(data, { origin: origin.trim(), destination: destination.trim() });
      navigate('/results');
    } catch (err) {
      setError(err.message || 'Failed to fetch routes. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex-1 px-4 pt-6 pb-24">
      {/* Hero */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-sky-100 mb-4">
          <MapPin size={32} className="text-sky-500" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900">SGTravelBud</h1>
        <p className="text-sm text-slate-500 mt-1">Smart routes for Singapore</p>
      </div>

      <form onSubmit={handleSearch} className="space-y-4">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4 space-y-3">
          <PlaceInput value={origin} onChange={setOrigin}
            placeholder="Where from?" dotColor="bg-emerald-400 ring-2 ring-emerald-100" />
          <PlaceInput value={destination} onChange={setDestination}
            placeholder="Where to?" dotColor="bg-red-400 ring-2 ring-red-100" />
          {samePlace && (
            <p className="text-xs text-red-500 flex items-center gap-1">
              <AlertCircle size={12} /> Origin and destination cannot be the same
            </p>
          )}
        </div>

        {/* Quick places */}
        <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
          {POPULAR_PLACES.map(place => (
            <button key={place} type="button"
              onClick={() => { if (!origin.trim()) setOrigin(place); else setDestination(place); }}
              className="shrink-0 px-3 py-1.5 rounded-full bg-white border border-slate-200 text-xs font-medium text-slate-600 hover:border-sky-300 hover:text-sky-600 transition-colors">
              {place}
            </button>
          ))}
        </div>

        {/* Mode toggles */}
        <div className="space-y-2">
          <span className="text-xs font-medium text-slate-500">Travel modes</span>
          <div className="grid grid-cols-2 gap-2">
            {modeButtons.map(({ key, label, icon: Icon, sub }) => (
              <button key={key} type="button" onClick={() => toggleMode(key)}
                className={`flex items-center gap-3 py-3 px-4 rounded-xl border-2 transition-all text-left
                  ${modes[key] ? 'border-sky-500 bg-sky-50' : 'border-slate-100 bg-white opacity-50'}`}>
                <Icon size={20} className={modes[key] ? 'text-sky-600' : 'text-slate-400'} />
                <div>
                  <span className={`text-xs font-semibold block ${modes[key] ? 'text-sky-700' : 'text-slate-500'}`}>{label}</span>
                  <span className="text-[10px] text-slate-400">{sub}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Advanced: Priorities + Constraints */}
        <button type="button" onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-1.5 text-xs font-medium text-slate-500 mx-auto">
          <SlidersHorizontal size={14} />
          {showAdvanced ? 'Hide' : 'Show'} priorities & constraints
        </button>

        {showAdvanced && (
          <div className="space-y-4">
            {/* Weight sliders */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4 space-y-3">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Priorities</h3>
              {[
                { key: 'time', label: 'Travel Time' },
                { key: 'cost', label: 'Cost' },
                { key: 'risk', label: 'Risk', sub: 'crowding + delay' },
                { key: 'comfort', label: 'Comfort', sub: 'walking + transfers' },
              ].map(({ key, label, sub }) => (
                <div key={key} className="flex items-center gap-3">
                  <div className="w-20">
                    <span className="text-xs font-medium text-slate-600">{label}</span>
                    {sub && <span className="text-[9px] text-slate-400 block">{sub}</span>}
                  </div>
                  <input type="range" min="0" max="1" step="0.05"
                    value={weights[key]}
                    onChange={e => setWeights(prev => ({ ...prev, [key]: parseFloat(e.target.value) }))}
                    className="flex-1 h-1.5 accent-sky-500" />
                  <span className="text-xs font-mono text-slate-400 w-8 text-right">
                    {weights[key].toFixed(2)}
                  </span>
                </div>
              ))}
            </div>

            {/* Hard constraints */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4 space-y-3">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Constraints</h3>
              <p className="text-[10px] text-slate-400">Routes that exceed these limits will be excluded</p>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[10px] text-slate-500 mb-1 block flex items-center gap-1">
                    <Footprints size={10} /> Max walk
                  </label>
                  <div className="relative">
                    <input type="number" min="1" max="60" placeholder="Any"
                      value={constraints.max_walk_min}
                      onChange={e => setConstraints(prev => ({ ...prev, max_walk_min: e.target.value }))}
                      className="w-full px-2 py-2 pr-8 rounded-lg border border-slate-200 bg-slate-50 text-xs focus:outline-none focus:ring-2 focus:ring-sky-500/30" />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-slate-400">min</span>
                  </div>
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 mb-1 block flex items-center gap-1">
                    <ArrowLeftRight size={10} /> Max transfers
                  </label>
                  <input type="number" min="0" max="10" placeholder="Any"
                    value={constraints.max_transfers}
                    onChange={e => setConstraints(prev => ({ ...prev, max_transfers: e.target.value }))}
                    className="w-full px-2 py-2 rounded-lg border border-slate-200 bg-slate-50 text-xs focus:outline-none focus:ring-2 focus:ring-sky-500/30" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 mb-1 block">Max budget</label>
                  <div className="relative">
                    <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[10px] text-slate-400">$</span>
                    <input type="number" min="0.5" step="0.5" placeholder="Any"
                      value={constraints.max_budget}
                      onChange={e => setConstraints(prev => ({ ...prev, max_budget: e.target.value }))}
                      className="w-full pl-5 pr-2 py-2 rounded-lg border border-slate-200 bg-slate-50 text-xs focus:outline-none focus:ring-2 focus:ring-sky-500/30" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-600 text-sm rounded-xl px-4 py-3 border border-red-100 flex items-start gap-2">
            <AlertCircle size={16} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <button type="submit" disabled={!canSearch}
          className="w-full bg-sky-500 text-white font-semibold py-3.5 px-6 rounded-xl active:bg-sky-700 transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
          {loading ? (
            <><Loader2 size={18} className="animate-spin" /> Finding routes...</>
          ) : (
            <><Search size={18} /> Find Routes</>
          )}
        </button>
      </form>
    </div>
  );
}
