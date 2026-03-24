import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin, Clock, Loader2, RefreshCw } from 'lucide-react';
import RouteCard from '../components/RouteCard';
import TimeCompare from '../components/TimeCompare';
import { fetchCompare } from '../utils/api';

export default function ResultsPage({ results, query, selectedRoute, onSelectRoute, onRefresh }) {
  const navigate = useNavigate();
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const routes = results?.routes || [];
  const trip = results?.trip;
  const weights = trip
    ? { time: trip.wt_time, cost: trip.wt_cost, risk: trip.wt_risk, comfort: trip.wt_comfort }
    : { time: 0.25, cost: 0.25, risk: 0.25, comfort: 0.25 };

  async function handleRefresh() {
    if (!onRefresh || refreshing) return;
    setRefreshing(true);
    try { await onRefresh(); } catch {} finally { setRefreshing(false); }
  }

  async function handleCompare() {
    if (!query?.origin || !query?.destination) return;
    setCompareLoading(true);
    try {
      const data = await fetchCompare({
        origin: query.origin,
        destination: query.destination,
        wt_time: weights.time,
        wt_cost: weights.cost,
        wt_risk: weights.risk,
        wt_comfort: weights.comfort,
      });
      setCompareData(data);
    } catch {} finally { setCompareLoading(false); }
  }

  if (!routes.length) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-4 pb-24">
        <div className="text-center animate-fade-up">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl glass mb-4">
            <MapPin size={28} className="text-slate-500" />
          </div>
          <h2 className="text-lg font-semibold text-slate-200 mb-1 font-display">No routes yet</h2>
          <p className="text-sm text-slate-500 mb-4">Search for a route to see results here</p>
          <button onClick={() => navigate('/')} className="btn-primary py-2.5 px-5 rounded-xl text-sm font-display">
            Search Routes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 px-4 pt-4 pb-24">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4 animate-fade-up">
        <button onClick={() => navigate('/')} className="p-2 -ml-2 rounded-xl hover:bg-white/[0.05] transition-colors">
          <ArrowLeft size={20} className="text-slate-400" />
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-[11px] text-slate-500 truncate font-display">
            {query?.origin} &rarr; {query?.destination}
          </p>
          <h2 className="text-lg font-bold text-white font-display">
            {routes.length} route{routes.length !== 1 ? 's' : ''} found
          </h2>
        </div>
        <button onClick={handleRefresh} disabled={refreshing}
          className="p-2 rounded-xl hover:bg-white/[0.05] transition-colors disabled:opacity-50"
          title="Refresh routes">
          <RefreshCw size={17} className={`text-slate-400 ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Backend message */}
      {results?.message && (
        <div className="bg-amber-500/10 text-amber-300 text-[11px] rounded-xl px-3 py-2 mb-3 border border-amber-500/20 animate-fade-up delay-1">
          {results.message}
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-3 mb-4 px-1 animate-fade-up delay-1">
        <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span className="w-2 h-2 rounded-full bg-emerald-400" /> Low
        </span>
        <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span className="w-2 h-2 rounded-full bg-amber-400" /> Medium
        </span>
        <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span className="w-2 h-2 rounded-full bg-red-400" /> High
        </span>
      </div>

      {/* Compare button */}
      <button onClick={handleCompare} disabled={compareLoading}
        className="w-full mb-3 flex items-center justify-center gap-2 glass glass-hover py-2.5 px-4 rounded-xl text-[11px] font-semibold text-amber-400/80 font-display transition-all disabled:opacity-50 animate-fade-up delay-2">
        {compareLoading ? (
          <><Loader2 size={13} className="animate-spin" /> Comparing...</>
        ) : (
          <><Clock size={13} /> Compare Departure Times</>
        )}
      </button>

      {/* Route cards */}
      <div className="space-y-3">
        {routes.map((route, i) => (
          <div key={i} className={`animate-fade-up delay-${Math.min(i + 2, 5)}`}>
            <RouteCard
              route={route}
              rank={i}
              selected={selectedRoute === route}
              onSelect={onSelectRoute}
              weights={weights}
            />
          </div>
        ))}
      </div>

      {/* Time comparison modal */}
      {compareData && (
        <TimeCompare data={compareData} onClose={() => setCompareData(null)} />
      )}

      {/* Map CTA */}
      {selectedRoute && (
        <div className="fixed bottom-20 left-4 right-4 z-40 max-w-lg mx-auto">
          <button onClick={() => navigate('/map')}
            className="w-full btn-primary py-3 rounded-xl shadow-lg flex items-center justify-center gap-2 font-display font-semibold text-sm"
            style={{ boxShadow: '0 4px 30px rgba(232,152,58,0.25)' }}>
            <MapPin size={17} /> View on Map
          </button>
        </div>
      )}
    </div>
  );
}
