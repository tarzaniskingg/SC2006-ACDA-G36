import { useState } from 'react';
import { Search, X, Loader2, ChevronUp, ChevronDown, RefreshCw, ArrowUpDown, Bus, Car, SlidersHorizontal, Footprints, ArrowLeftRight, Clock } from 'lucide-react';
import RouteMap from '../components/RouteMap';
import RouteCard from '../components/RouteCard';
import TimeCompare from '../components/TimeCompare';
import PlaceInput from '../components/PlaceInput';
import { fetchRoutes, fetchCompare } from '../utils/api';
import { formatDuration, formatCost } from '../utils/helpers';

const SHEET_PEEK = 0;
const SHEET_RESULTS = 1;

export default function MainView({ results, query, selectedRoute, onSelectRoute, onResults, onRefresh, initialForm }) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [sheetState, setSheetState] = useState(results?.routes?.length ? SHEET_RESULTS : SHEET_PEEK);

  const [origin, setOrigin] = useState(initialForm?.origin || '');
  const [destination, setDestination] = useState(initialForm?.destination || '');
  const [modes, setModes] = useState(initialForm?.modes || { transit: true, driving: true });
  const [weights, setWeights] = useState(initialForm?.weights || { time: 0.25, cost: 0.25, risk: 0.25, comfort: 0.25 });
  const [constraints, setConstraints] = useState(initialForm?.constraints || { max_walk_min: '', max_transfers: '', max_budget: '' });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);

  const routes = results?.routes || [];
  const trip = results?.trip;
  const tripWeights = trip
    ? { time: trip.wt_time, cost: trip.wt_cost, risk: trip.wt_risk, comfort: trip.wt_comfort }
    : weights;

  // Bottom sheet takes ~55vh when open. Convert to pixels for map padding.
  // window.innerHeight * 0.55 gives us roughly how much the sheet covers.
  const sheetPixels = typeof window !== 'undefined' ? Math.round(window.innerHeight * 0.55) : 400;
  const mapBottomPad = routes.length > 0 && sheetState === SHEET_RESULTS ? sheetPixels + 20 : 100;

  function swapPlaces() {
    setOrigin(prev => { const tmp = prev; setDestination(origin); return destination; });
  }

  function toggleMode(key) {
    setModes(prev => {
      const next = { ...prev, [key]: !prev[key] };
      return (!next.transit && !next.driving) ? prev : next;
    });
  }

  async function handleSearch() {
    const o = origin.trim(), d = destination.trim();
    if (o.length < 2 || d.length < 2 || o.toLowerCase() === d.toLowerCase()) return;
    setLoading(true);
    setError(null);
    try {
      const params = {
        origin: o, destination: d,
        include_transit: modes.transit, include_driving: modes.driving,
        wt_time: weights.time, wt_cost: weights.cost,
        wt_risk: weights.risk, wt_comfort: weights.comfort,
      };
      if (constraints.max_walk_min) params.max_walk_min = parseInt(constraints.max_walk_min);
      if (constraints.max_transfers) params.max_transfers = parseInt(constraints.max_transfers);
      if (constraints.max_budget) params.max_budget = parseFloat(constraints.max_budget);
      const data = await fetchRoutes(params);
      if (!data.routes?.length) { setError(data.message || 'No routes found.'); return; }
      onResults(data, { origin: o, destination: d }, { origin: o, destination: d, modes, weights, constraints });
      setSearchOpen(false);
      setSheetState(SHEET_RESULTS);
    } catch (err) {
      setError(err.message || 'Failed to fetch routes.');
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    if (refreshing) return;
    setRefreshing(true);
    try { await onRefresh(); } catch {} finally { setRefreshing(false); }
  }

  async function handleCompare() {
    if (!query?.origin || !query?.destination || compareLoading) return;
    setCompareLoading(true);
    try {
      const data = await fetchCompare({ origin: query.origin, destination: query.destination, ...tripWeights });
      setCompareData(data);
    } catch {} finally { setCompareLoading(false); }
  }

  const canSearch = origin.trim().length >= 2 && destination.trim().length >= 2 &&
    origin.trim().toLowerCase() !== destination.trim().toLowerCase() && !loading;

  return (
    <div className="relative w-full h-full overflow-hidden">
      {/* ===== MAP ===== */}
      <div className="absolute inset-0 z-0">
        <RouteMap route={selectedRoute} query={query} bottomPadding={mapBottomPad} />
      </div>

      {/* ===== FLOATING SEARCH BAR ===== */}
      {!searchOpen && (
        <div className="absolute top-3 left-3 right-3 z-20 anim-fade-up">
          <button onClick={() => setSearchOpen(true)}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl panel border border-white/[0.08] shadow-lg shadow-black/30">
            <Search size={18} className="text-slate-400 shrink-0" />
            {query ? (
              <div className="flex-1 min-w-0 text-left">
                <span className="text-[13px] text-white font-medium font-display truncate block">{query.origin}</span>
                <span className="text-[11px] text-slate-400 truncate block">to {query.destination}</span>
              </div>
            ) : (
              <span className="text-[13px] text-slate-400 font-display">Where are you going?</span>
            )}
          </button>
        </div>
      )}

      {/* ===== SEARCH OVERLAY ===== */}
      {searchOpen && (
        <div className="absolute inset-0 z-30 flex flex-col anim-fade-in" style={{ background: 'var(--color-panel-solid)' }}>
          <div className="flex items-center gap-2 px-4 pt-4 pb-2 shrink-0">
            <button onClick={() => setSearchOpen(false)} className="p-2 rounded-xl hover:bg-white/[0.06] transition-colors">
              <X size={20} className="text-slate-400" />
            </button>
            <h2 className="text-base font-semibold text-white font-display flex-1">Plan Route</h2>
          </div>

          <div className="flex-1 overflow-y-auto px-4 pb-4">
            <div className="space-y-4">
              {/* Origin / Destination with swap button between them */}
              <div className="glass rounded-2xl p-3 relative">
                <PlaceInput value={origin} onChange={setOrigin}
                  placeholder="Origin" dotColor="bg-emerald-400 ring-2 ring-emerald-400/20" />
                <div className="flex items-center my-1.5">
                  <div className="flex-1 h-px bg-white/[0.06]" />
                  <button onClick={swapPlaces}
                    className="mx-2 p-1 rounded-full bg-white/[0.08] hover:bg-white/[0.14] border border-white/[0.12] transition-colors"
                    title="Swap origin and destination">
                    <ArrowUpDown size={12} className="text-slate-400" />
                  </button>
                  <div className="flex-1 h-px bg-white/[0.06]" />
                </div>
                <PlaceInput value={destination} onChange={setDestination}
                  placeholder="Destination" dotColor="bg-red-400 ring-2 ring-red-400/20" />
              </div>

              {/* Mode toggles */}
              <div className="grid grid-cols-2 gap-2">
                {[
                  { key: 'transit', label: 'Public Transit', icon: Bus },
                  { key: 'driving', label: 'Taxi / Drive', icon: Car },
                ].map(({ key, label, icon: Icon }) => (
                  <button key={key} type="button" onClick={() => toggleMode(key)}
                    className={`flex items-center gap-2.5 py-3 px-3.5 rounded-xl transition-all text-left border
                      ${modes[key]
                        ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                        : 'bg-white/[0.03] border-white/[0.08] text-slate-500 opacity-60'}`}>
                    <Icon size={18} />
                    <span className="text-[12px] font-semibold font-display">{label}</span>
                  </button>
                ))}
              </div>

              {/* Advanced */}
              <button onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-1.5 text-[11px] text-slate-500 font-display mx-auto hover:text-slate-300 transition-colors">
                <SlidersHorizontal size={12} />
                {showAdvanced ? 'Hide' : 'Show'} priorities & constraints
              </button>

              {showAdvanced && (
                <div className="space-y-3 anim-fade-up">
                  <div className="glass rounded-xl p-3 space-y-3">
                    <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider font-display">Priorities</span>
                    {['time', 'cost', 'risk', 'comfort'].map(key => (
                      <div key={key} className="flex items-center gap-2">
                        <span className="text-[11px] text-slate-400 w-14 capitalize">{key}</span>
                        <input type="range" min="0" max="1" step="0.05" value={weights[key]}
                          onChange={e => setWeights(prev => ({ ...prev, [key]: parseFloat(e.target.value) }))}
                          className="flex-1" />
                        <span className="text-[10px] font-mono text-slate-500 w-7 text-right">{weights[key].toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                  <div className="glass rounded-xl p-3 space-y-2">
                    <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider font-display">Constraints</span>
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <label className="text-[9px] text-slate-500 mb-0.5 block"><Footprints size={9} className="inline" /> Walk</label>
                        <input type="number" min="1" max="60" placeholder="Any" value={constraints.max_walk_min}
                          onChange={e => setConstraints(p => ({ ...p, max_walk_min: e.target.value }))}
                          className="input-dark w-full px-2 py-1.5 rounded-lg text-[11px]" />
                      </div>
                      <div>
                        <label className="text-[9px] text-slate-500 mb-0.5 block"><ArrowLeftRight size={9} className="inline" /> Transfers</label>
                        <input type="number" min="0" max="10" placeholder="Any" value={constraints.max_transfers}
                          onChange={e => setConstraints(p => ({ ...p, max_transfers: e.target.value }))}
                          className="input-dark w-full px-2 py-1.5 rounded-lg text-[11px]" />
                      </div>
                      <div>
                        <label className="text-[9px] text-slate-500 mb-0.5 block">Budget</label>
                        <input type="number" min="0.5" step="0.5" placeholder="Any" value={constraints.max_budget}
                          onChange={e => setConstraints(p => ({ ...p, max_budget: e.target.value }))}
                          className="input-dark w-full px-2 py-1.5 rounded-lg text-[11px]" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {error && (
                <div className="bg-red-500/10 text-red-400 text-[12px] rounded-xl px-3 py-2.5 border border-red-500/20">{error}</div>
              )}

              <button onClick={handleSearch} disabled={!canSearch}
                className="w-full btn-accent py-3 rounded-xl text-[13px] flex items-center justify-center gap-2">
                {loading ? <><Loader2 size={16} className="animate-spin" /> Searching...</> : <><Search size={16} /> Find Routes</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ===== BOTTOM RESULTS SHEET ===== */}
      {routes.length > 0 && !searchOpen && (
        <div className={`absolute left-0 right-0 bottom-0 z-20 flex flex-col panel rounded-t-3xl border-t border-white/[0.08] shadow-2xl shadow-black/40 transition-[max-height] duration-300 ease-out overflow-hidden
          ${sheetState === SHEET_PEEK ? 'max-h-[100px]' : 'max-h-[55vh]'}`}>

          {/* Handle */}
          <button onClick={() => setSheetState(s => s === SHEET_RESULTS ? SHEET_PEEK : SHEET_RESULTS)}
            className="w-full pt-2 pb-1 flex flex-col items-center shrink-0">
            <div className="sheet-handle" />
          </button>

          {/* Summary bar — always visible */}
          <div className="flex items-center gap-2 px-4 pb-2 shrink-0">
            <div className="flex-1 min-w-0">
              <span className="text-[13px] font-semibold text-white font-display">
                {routes.length} route{routes.length !== 1 ? 's' : ''}
              </span>
              <span className="text-[11px] text-slate-500 ml-2 font-display">
                Best: {formatDuration(routes[0]?.time_min)} &middot; {formatCost(routes[0]?.cost_est)}
              </span>
            </div>
            <button onClick={handleRefresh} disabled={refreshing}
              className="p-1.5 rounded-lg hover:bg-white/[0.06] transition-colors shrink-0" title="Refresh">
              <RefreshCw size={15} className={`text-slate-400 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
            <button onClick={() => setSheetState(s => s === SHEET_RESULTS ? SHEET_PEEK : SHEET_RESULTS)}
              className="p-1.5 rounded-lg hover:bg-white/[0.06] transition-colors shrink-0">
              {sheetState >= SHEET_RESULTS
                ? <ChevronDown size={16} className="text-slate-400" />
                : <ChevronUp size={16} className="text-slate-400" />}
            </button>
          </div>

          {/* Scrollable card list */}
          {sheetState >= SHEET_RESULTS && (
            <div className="overflow-y-auto overscroll-contain px-4 pb-4 space-y-2.5"
              style={{ minHeight: 0 }}>
              {/* Compare button */}
              <button onClick={handleCompare} disabled={compareLoading}
                className="w-full btn-ghost py-2 rounded-xl text-[11px] font-display font-medium flex items-center justify-center gap-1.5 shrink-0">
                {compareLoading
                  ? <><Loader2 size={12} className="animate-spin" /> Comparing...</>
                  : <><Clock size={12} /> Compare Departure Times</>}
              </button>

              {routes.map((route, i) => (
                <RouteCard
                  key={i}
                  route={route}
                  rank={i}
                  selected={selectedRoute === route}
                  onSelect={onSelectRoute}
                  weights={tripWeights}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Time comparison modal */}
      {compareData && <TimeCompare data={compareData} onClose={() => setCompareData(null)} />}
    </div>
  );
}
