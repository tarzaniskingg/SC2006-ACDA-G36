import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ChevronLeft, ChevronRight } from 'lucide-react';
import RouteMap from '../components/RouteMap';
import RiskBadge from '../components/RiskBadge';
import { formatDuration, formatCost } from '../utils/helpers';

export default function MapPage({ results, query, selectedRoute, onSelectRoute }) {
  const navigate = useNavigate();
  const routes = results?.routes || [];
  const currentIdx = routes.indexOf(selectedRoute);

  function prev() { if (currentIdx > 0) onSelectRoute(routes[currentIdx - 1]); }
  function next() { if (currentIdx < routes.length - 1) onSelectRoute(routes[currentIdx + 1]); }

  if (!selectedRoute) {
    return (
      <div className="flex items-center justify-center px-4" style={{ height: 'calc(100vh - 4rem)' }}>
        <div className="text-center animate-fade-up">
          <p className="text-sm text-slate-500 mb-4 font-display">Select a route from Results to view on map</p>
          <button onClick={() => navigate('/results')} className="btn-primary py-2.5 px-5 rounded-xl text-sm font-display">
            View Routes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 4rem)' }}>
      {/* Top bar */}
      <div className="flex items-center gap-2 px-4 py-3 shrink-0 border-b border-white/[0.06] relative z-10"
        style={{ background: 'rgba(8, 12, 24, 0.85)', backdropFilter: 'blur(16px)' }}>
        <button onClick={() => navigate('/results')} className="p-1.5 rounded-lg hover:bg-white/[0.06] transition-colors">
          <ArrowLeft size={18} className="text-slate-400" />
        </button>
        <div className="flex-1 text-center">
          <span className="text-sm font-semibold text-white font-display">
            Route {currentIdx + 1} of {routes.length}
          </span>
        </div>
        <div className="flex gap-1">
          <button onClick={prev} disabled={currentIdx <= 0}
            className="p-1.5 rounded-lg hover:bg-white/[0.06] disabled:opacity-30 transition-colors">
            <ChevronLeft size={18} className="text-slate-300" />
          </button>
          <button onClick={next} disabled={currentIdx >= routes.length - 1}
            className="p-1.5 rounded-lg hover:bg-white/[0.06] disabled:opacity-30 transition-colors">
            <ChevronRight size={18} className="text-slate-300" />
          </button>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <div className="absolute inset-0">
          <RouteMap route={selectedRoute} query={query} />
        </div>
      </div>

      {/* Bottom info */}
      <div className="px-4 py-3 shrink-0 border-t border-white/[0.06]"
        style={{ background: 'rgba(8, 12, 24, 0.92)', backdropFilter: 'blur(16px)' }}>
        <div className="flex items-center justify-between mb-2">
          <div>
            <span className="text-sm font-bold text-white font-display">
              {formatDuration(selectedRoute.time_min)}
            </span>
            <span className="text-[11px] text-slate-500 ml-2">
              {selectedRoute.distance_km} km
            </span>
          </div>
          <span className="text-sm font-semibold text-slate-200 font-display">
            {formatCost(selectedRoute.cost_est)}
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          <RiskBadge category={selectedRoute.risk_crowding_cat} label="crowd" />
          <RiskBadge category={selectedRoute.risk_delay_cat} label="delay" />
          {selectedRoute.transfers != null && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-white/5 text-slate-400 ring-1 ring-white/10">
              {selectedRoute.transfers} transfer{selectedRoute.transfers !== 1 ? 's' : ''}
            </span>
          )}
          {selectedRoute.category && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20">
              {selectedRoute.category}
            </span>
          )}
        </div>
        {selectedRoute.explanation && (
          <p className="text-[11px] text-slate-500 mt-2">{selectedRoute.explanation}</p>
        )}
      </div>
    </div>
  );
}
