import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ChevronLeft, ChevronRight } from 'lucide-react';
import RouteMap from '../components/RouteMap';
import RiskBadge from '../components/RiskBadge';
import { formatDuration, formatCost } from '../utils/helpers';

export default function MapPage({ results, query, selectedRoute, onSelectRoute }) {
  const navigate = useNavigate();
  const routes = results?.routes || [];

  const currentIdx = routes.indexOf(selectedRoute);

  function prev() {
    if (currentIdx > 0) onSelectRoute(routes[currentIdx - 1]);
  }
  function next() {
    if (currentIdx < routes.length - 1) onSelectRoute(routes[currentIdx + 1]);
  }

  if (!selectedRoute) {
    return (
      <div className="flex items-center justify-center px-4" style={{ height: 'calc(100vh - 4rem)' }}>
        <div className="text-center">
          <p className="text-sm text-slate-500 mb-4">Select a route from Results to view on map</p>
          <button
            onClick={() => navigate('/results')}
            className="bg-sky-500 text-white font-semibold py-2.5 px-5 rounded-xl text-sm"
          >
            View Routes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 4rem)' }}>
      {/* Top bar */}
      <div className="flex items-center gap-2 px-4 py-3 bg-white/80 backdrop-blur border-b border-slate-100 shrink-0">
        <button onClick={() => navigate('/results')} className="p-1.5 rounded-lg hover:bg-slate-100">
          <ArrowLeft size={18} className="text-slate-600" />
        </button>
        <div className="flex-1 text-center">
          <span className="text-sm font-semibold text-slate-800">
            Route {currentIdx + 1} of {routes.length}
          </span>
        </div>
        <div className="flex gap-1">
          <button onClick={prev} disabled={currentIdx <= 0} className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-30">
            <ChevronLeft size={18} />
          </button>
          <button onClick={next} disabled={currentIdx >= routes.length - 1} className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-30">
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      {/* Map — takes all remaining space */}
      <div className="flex-1 relative">
        <div className="absolute inset-0">
          <RouteMap route={selectedRoute} query={query} />
        </div>
      </div>

      {/* Bottom info card */}
      <div className="bg-white border-t border-slate-100 px-4 py-3 shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div>
            <span className="text-sm font-bold text-slate-800">
              {formatDuration(selectedRoute.time_min)}
            </span>
            <span className="text-xs text-slate-400 ml-2">
              {selectedRoute.distance_km} km
            </span>
          </div>
          <span className="text-sm font-semibold text-slate-600">
            {formatCost(selectedRoute.cost_est)}
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          <RiskBadge category={selectedRoute.risk_crowding_cat} label="crowd" />
          <RiskBadge category={selectedRoute.risk_delay_cat} label="delay" />
          {selectedRoute.transfers != null && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600">
              {selectedRoute.transfers} transfer{selectedRoute.transfers !== 1 ? 's' : ''}
            </span>
          )}
          {selectedRoute.category && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-50 text-sky-600">
              {selectedRoute.category}
            </span>
          )}
        </div>
        {selectedRoute.explanation && (
          <p className="text-xs text-slate-500 mt-2">{selectedRoute.explanation}</p>
        )}
      </div>
    </div>
  );
}
