import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin, Clock, Loader2 } from 'lucide-react';
import RouteCard from '../components/RouteCard';
import TimeCompare from '../components/TimeCompare';
import { fetchCompare } from '../utils/api';

export default function ResultsPage({ results, query, selectedRoute, onSelectRoute }) {
  const navigate = useNavigate();
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const routes = results?.routes || [];
  const trip = results?.trip;
  const weights = trip
    ? { time: trip.wt_time, cost: trip.wt_cost, risk: trip.wt_risk, comfort: trip.wt_comfort }
    : { time: 0.25, cost: 0.25, risk: 0.25, comfort: 0.25 };

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
    } catch {
      // silently fail
    } finally {
      setCompareLoading(false);
    }
  }

  if (!routes.length) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-4 pb-24">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-100 mb-4">
            <MapPin size={28} className="text-slate-400" />
          </div>
          <h2 className="text-lg font-semibold text-slate-700 mb-1">No routes yet</h2>
          <p className="text-sm text-slate-500 mb-4">Search for a route to see results here</p>
          <button
            onClick={() => navigate('/')}
            className="bg-sky-500 text-white font-semibold py-2.5 px-5 rounded-xl text-sm"
          >
            Search Routes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 px-4 pt-4 pb-24">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={() => navigate('/')}
          className="p-2 -ml-2 rounded-xl hover:bg-slate-100 transition-colors"
        >
          <ArrowLeft size={20} className="text-slate-600" />
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-xs text-slate-500 truncate">
            {query?.origin} &rarr; {query?.destination}
          </p>
          <h2 className="text-lg font-bold text-slate-900">
            {routes.length} route{routes.length !== 1 ? 's' : ''} found
          </h2>
        </div>
      </div>

      {/* Message from backend */}
      {results?.message && (
        <div className="bg-amber-50 text-amber-700 text-xs rounded-xl px-3 py-2 mb-3 border border-amber-100">
          {results.message}
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-3 mb-4 px-1">
        <span className="flex items-center gap-1 text-[11px] text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400" /> Low
        </span>
        <span className="flex items-center gap-1 text-[11px] text-slate-400">
          <span className="w-2 h-2 rounded-full bg-amber-400" /> Medium
        </span>
        <span className="flex items-center gap-1 text-[11px] text-slate-400">
          <span className="w-2 h-2 rounded-full bg-red-400" /> High
        </span>
      </div>

      {/* Compare departure times button (Feature 1) */}
      <button
        onClick={handleCompare}
        disabled={compareLoading}
        className="w-full mb-3 flex items-center justify-center gap-2 bg-white border-2 border-sky-200 text-sky-600 font-semibold py-2.5 px-4 rounded-xl text-xs hover:bg-sky-50 transition-colors disabled:opacity-50"
      >
        {compareLoading ? (
          <><Loader2 size={14} className="animate-spin" /> Comparing...</>
        ) : (
          <><Clock size={14} /> Compare Departure Times</>
        )}
      </button>

      {/* Route cards */}
      <div className="space-y-3">
        {routes.map((route, i) => (
          <RouteCard
            key={i}
            route={route}
            rank={i}
            selected={selectedRoute === route}
            onSelect={onSelectRoute}
            weights={weights}
          />
        ))}
      </div>

      {/* Time comparison modal (Feature 1) */}
      {compareData && (
        <TimeCompare data={compareData} onClose={() => setCompareData(null)} />
      )}

      {/* View on map CTA */}
      {selectedRoute && (
        <div className="fixed bottom-20 left-4 right-4 z-40 max-w-lg mx-auto">
          <button
            onClick={() => navigate('/map')}
            className="w-full bg-sky-500 text-white font-semibold py-3 rounded-xl shadow-lg shadow-sky-500/25 flex items-center justify-center gap-2"
          >
            <MapPin size={18} />
            View on Map
          </button>
        </div>
      )}
    </div>
  );
}
