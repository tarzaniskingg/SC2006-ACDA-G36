import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, MapPin, Clock, Loader2, RefreshCw } from 'lucide-react';
import RouteCard from '../components/RouteCard';
import TimeCompare from '../components/TimeCompare';
import { fetchCompare } from '../utils/api';

export default function ResultsPage({ results, query, selectedRoute, onSelectRoute, onRefresh }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [comparePrefetch, setComparePrefetch] = useState({});
  const [refreshing, setRefreshing] = useState(false);
  const routes = results?.routes || [];
  const trip = results?.trip;
  const weights = trip
    ? { time: trip.wt_time, cost: trip.wt_cost, risk: trip.wt_risk, comfort: trip.wt_comfort }
    : { time: 0.25, cost: 0.25, risk: 0.25, comfort: 0.25 };

  // Pre-fetch compare data silently per category
  const selectedCategory = selectedRoute?.category;
  useEffect(() => {
    if (!query?.origin || !query?.destination || !selectedCategory) return;
    if (comparePrefetch[selectedCategory]) return;
    let cancelled = false;
    fetchCompare({
      origin: query.origin, destination: query.destination,
      category: selectedCategory,
      wt_time: weights.time, wt_cost: weights.cost,
      wt_risk: weights.risk, wt_comfort: weights.comfort,
    }).then(data => {
      if (!cancelled) setComparePrefetch(prev => ({ ...prev, [selectedCategory]: data }));
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [selectedCategory, query?.origin, query?.destination]);

  async function handleRefresh() {
    if (!onRefresh || refreshing) return;
    setRefreshing(true);
    try { await onRefresh(); } catch {} finally { setRefreshing(false); }
  }

  function handleCompare() {
    if (!selectedRoute) return;
    const cached = comparePrefetch[selectedRoute.category];
    if (cached) { setCompareData(cached); return; }
    if (!query?.origin || !query?.destination || compareLoading) return;
    setCompareLoading(true);
    fetchCompare({
      origin: query.origin, destination: query.destination,
      category: selectedRoute.category,
      wt_time: weights.time, wt_cost: weights.cost,
      wt_risk: weights.risk, wt_comfort: weights.comfort,
    }).then(data => setCompareData(data))
      .catch(() => {})
      .finally(() => setCompareLoading(false));
  }

  if (!routes.length) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-4 pb-24">
        <div className="text-center animate-fade-up">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl glass mb-4">
            <MapPin size={28} className="text-slate-500" />
          </div>
          <h2 className="text-lg font-semibold text-slate-200 mb-1 font-display">{t('results.noRoutes')}</h2>
          <p className="text-sm text-slate-500 mb-4">{t('results.searchPrompt')}</p>
          <button onClick={() => navigate('/')} className="btn-primary py-2.5 px-5 rounded-xl text-sm font-display">
            {t('results.searchRoutes')}
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
            {t('results.routesFound', { count: routes.length })}
          </h2>
        </div>
        <button onClick={handleRefresh} disabled={refreshing}
          className="p-2 rounded-xl hover:bg-white/[0.05] transition-colors disabled:opacity-50"
          title={t('results.refresh')}>
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
          <span className="w-2 h-2 rounded-full bg-emerald-400" /> {t('risk.low')}
        </span>
        <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span className="w-2 h-2 rounded-full bg-amber-400" /> {t('risk.medium')}
        </span>
        <span className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span className="w-2 h-2 rounded-full bg-red-400" /> {t('risk.high')}
        </span>
      </div>

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

      {/* Floating buttons — Map left, Compare right */}
      {selectedRoute && (
        <div className="fixed bottom-20 left-4 right-4 z-40 max-w-lg mx-auto flex items-center gap-2">
          <button onClick={() => navigate('/map')}
            className="flex-1 btn-primary py-3 rounded-xl shadow-lg flex items-center justify-center gap-2 font-display font-semibold text-sm"
            style={{ boxShadow: '0 4px 30px rgba(232,152,58,0.25)' }}>
            <MapPin size={17} /> {t('results.viewOnMap')}
          </button>
          <button onClick={handleCompare} disabled={compareLoading}
            className="flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg font-display font-semibold text-[11px] transition-all active:scale-95 bg-amber-500/90 text-slate-900 hover:bg-amber-400"
            style={{ boxShadow: '0 4px 24px rgba(232,152,58,0.35)' }}>
            {compareLoading
              ? <Loader2 size={13} className="animate-spin" />
              : <Clock size={13} />}
            {t('results.compareDepart')}
          </button>
        </div>
      )}
    </div>
  );
}
