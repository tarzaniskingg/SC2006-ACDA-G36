import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, MapPin, Bus, Car, SlidersHorizontal, Loader2, AlertCircle, Footprints, ArrowLeftRight } from 'lucide-react';
import { fetchRoutes } from '../utils/api';
import PlaceInput from '../components/PlaceInput';

const POPULAR_PLACES = [
  'Changi Airport', 'Orchard Road', 'Marina Bay Sands', 'Sentosa',
  'NTU', 'NUS', 'Jurong East', 'Tampines Mall', 'Woodlands', 'Punggol',
];

export default function SearchPage({ onResults, initialForm }) {
  const navigate = useNavigate();
  const [origin, setOrigin] = useState(initialForm?.origin || '');
  const [destination, setDestination] = useState(initialForm?.destination || '');
  const [modes, setModes] = useState(initialForm?.modes || { transit: true, driving: true });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [weights, setWeights] = useState(initialForm?.weights || { time: 0.25, cost: 0.25, risk: 0.25, comfort: 0.25 });
  const [constraints, setConstraints] = useState(initialForm?.constraints || { max_walk_min: '', max_transfers: '', max_budget: '' });
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
      onResults(data, { origin: origin.trim(), destination: destination.trim() }, {
        origin: origin.trim(),
        destination: destination.trim(),
        modes,
        weights,
        constraints,
      });
      navigate('/results');
    } catch (err) {
      setError(err.message || 'Failed to fetch routes. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex-1 px-4 pt-8 pb-24">
      {/* Hero */}
      <div className="text-center mb-10 animate-fade-up">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-5 relative"
          style={{ background: 'linear-gradient(135deg, rgba(232,152,58,0.15), rgba(232,152,58,0.05))', border: '1px solid rgba(232,152,58,0.2)' }}>
          <MapPin size={28} className="text-amber-400" />
          <div className="absolute inset-0 rounded-2xl" style={{ boxShadow: '0 0 40px rgba(232,152,58,0.1)' }} />
        </div>
        <h1 className="font-display text-3xl font-bold text-white tracking-tight">SGTravelBud</h1>
        <p className="text-sm text-slate-400 mt-1.5 font-display font-light tracking-wide">Smart routes for Singapore</p>
      </div>

      <form onSubmit={handleSearch} className="space-y-4">
        {/* Origin/Destination */}
        <div className="glass rounded-2xl p-4 space-y-3 animate-fade-up delay-1">
          <PlaceInput value={origin} onChange={setOrigin}
            placeholder="Where from?" dotColor="bg-emerald-400 ring-2 ring-emerald-400/20" />
          <div className="h-px bg-white/[0.06] mx-2" />
          <PlaceInput value={destination} onChange={setDestination}
            placeholder="Where to?" dotColor="bg-red-400 ring-2 ring-red-400/20" />
          {samePlace && (
            <p className="text-xs text-red-400 flex items-center gap-1">
              <AlertCircle size={12} /> Origin and destination cannot be the same
            </p>
          )}
        </div>

        {/* Quick places */}
        <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 animate-fade-up delay-2">
          {POPULAR_PLACES.map(place => (
            <button key={place} type="button"
              onClick={() => { if (!origin.trim()) setOrigin(place); else setDestination(place); }}
              className="shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200
                bg-white/[0.04] border border-white/[0.08] text-slate-400
                hover:bg-amber-500/10 hover:border-amber-500/20 hover:text-amber-300">
              {place}
            </button>
          ))}
        </div>

        {/* Mode toggles */}
        <div className="space-y-2 animate-fade-up delay-3">
          <span className="text-xs font-medium text-slate-500 font-display uppercase tracking-wider">Travel modes</span>
          <div className="grid grid-cols-2 gap-2.5">
            {modeButtons.map(({ key, label, icon: Icon, sub }) => (
              <button key={key} type="button" onClick={() => toggleMode(key)}
                className={`flex items-center gap-3 py-3.5 px-4 rounded-xl transition-all duration-200 text-left
                  ${modes[key]
                    ? 'glass-active glow-amber'
                    : 'glass opacity-50 hover:opacity-70'}`}>
                <Icon size={20} className={modes[key] ? 'text-amber-400' : 'text-slate-500'} />
                <div>
                  <span className={`text-xs font-semibold block font-display ${modes[key] ? 'text-amber-200' : 'text-slate-400'}`}>{label}</span>
                  <span className="text-[10px] text-slate-500">{sub}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Advanced toggle */}
        <button type="button" onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-1.5 text-xs font-medium text-slate-500 mx-auto hover:text-slate-300 transition-colors font-display">
          <SlidersHorizontal size={13} />
          {showAdvanced ? 'Hide' : 'Show'} priorities & constraints
        </button>

        {showAdvanced && (
          <div className="space-y-4 animate-fade-up">
            {/* Weight sliders */}
            <div className="glass rounded-2xl p-4 space-y-3.5">
              <h3 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider font-display">Priorities</h3>
              {[
                { key: 'time', label: 'Travel Time' },
                { key: 'cost', label: 'Cost' },
                { key: 'risk', label: 'Risk', sub: 'crowding + delay' },
                { key: 'comfort', label: 'Comfort', sub: 'walking + transfers' },
              ].map(({ key, label, sub }) => (
                <div key={key} className="flex items-center gap-3">
                  <div className="w-20">
                    <span className="text-xs font-medium text-slate-300">{label}</span>
                    {sub && <span className="text-[9px] text-slate-500 block">{sub}</span>}
                  </div>
                  <input type="range" min="0" max="1" step="0.05"
                    value={weights[key]}
                    onChange={e => setWeights(prev => ({ ...prev, [key]: parseFloat(e.target.value) }))}
                    className="flex-1" />
                  <span className="text-xs font-mono text-slate-500 w-8 text-right">
                    {weights[key].toFixed(2)}
                  </span>
                </div>
              ))}
            </div>

            {/* Hard constraints */}
            <div className="glass rounded-2xl p-4 space-y-3">
              <h3 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider font-display">Constraints</h3>
              <p className="text-[10px] text-slate-500">Routes that exceed these limits will be excluded</p>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[10px] text-slate-500 mb-1 block flex items-center gap-1">
                    <Footprints size={10} /> Max walk
                  </label>
                  <div className="relative">
                    <input type="number" min="1" max="60" placeholder="Any"
                      value={constraints.max_walk_min}
                      onChange={e => setConstraints(prev => ({ ...prev, max_walk_min: e.target.value }))}
                      className="input-dark w-full px-2 py-2 pr-8 rounded-lg text-xs" />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-slate-500">min</span>
                  </div>
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 mb-1 block flex items-center gap-1">
                    <ArrowLeftRight size={10} /> Max transfers
                  </label>
                  <input type="number" min="0" max="10" placeholder="Any"
                    value={constraints.max_transfers}
                    onChange={e => setConstraints(prev => ({ ...prev, max_transfers: e.target.value }))}
                    className="input-dark w-full px-2 py-2 rounded-lg text-xs" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 mb-1 block">Max budget</label>
                  <div className="relative">
                    <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[10px] text-slate-500">$</span>
                    <input type="number" min="0.5" step="0.5" placeholder="Any"
                      value={constraints.max_budget}
                      onChange={e => setConstraints(prev => ({ ...prev, max_budget: e.target.value }))}
                      className="input-dark w-full pl-5 pr-2 py-2 rounded-lg text-xs" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 text-red-400 text-sm rounded-xl px-4 py-3 border border-red-500/20 flex items-start gap-2 animate-fade-up">
            <AlertCircle size={16} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <button type="submit" disabled={!canSearch}
          className="w-full btn-primary py-3.5 px-6 rounded-xl flex items-center justify-center gap-2 text-sm font-display font-semibold animate-fade-up delay-4">
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
