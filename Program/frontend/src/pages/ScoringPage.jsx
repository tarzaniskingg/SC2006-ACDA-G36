import { useNavigate } from 'react-router-dom';
import { BarChart3, Clock, AlertTriangle, DollarSign, Heart, Info, ArrowRight } from 'lucide-react';
import { formatDuration, formatCost, riskBadgeClass } from '../utils/helpers';
import CrowdingHeatmap from '../components/CrowdingHeatmap';

const DIMENSIONS = [
  { key: 'time', normKey: 'normalized_time', label: 'Time', icon: Clock, color: 'bg-blue-400', lightBg: 'bg-blue-500/10' },
  { key: 'cost', normKey: 'normalized_cost', label: 'Cost', icon: DollarSign, color: 'bg-emerald-400', lightBg: 'bg-emerald-500/10' },
  { key: 'risk', normKey: 'normalized_risk', label: 'Risk', icon: AlertTriangle, color: 'bg-red-400', lightBg: 'bg-red-500/10' },
  { key: 'comfort', normKey: 'normalized_comfort', label: 'Comfort', icon: Heart, color: 'bg-purple-400', lightBg: 'bg-purple-500/10' },
];

function ScoreBar({ value, color, label }) {
  const pct = Math.round((value ?? 0) * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] text-slate-400 w-20 shrink-0 font-display">{label}</span>
      <div className="flex-1 h-2.5 bg-white/[0.06] rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[11px] font-mono text-slate-500 w-10 text-right">{value?.toFixed(2) ?? '--'}</span>
    </div>
  );
}

function RouteScoreCard({ route, rank, weights }) {
  const rankLabels = ['Best', '2nd', '3rd'];
  const rankStyles = [
    'bg-gradient-to-r from-amber-500 to-amber-600 text-black',
    'bg-white/10 text-slate-300',
    'bg-white/5 text-slate-400',
  ];

  const contributions = DIMENSIONS.map(d => {
    const norm = route[d.normKey] ?? 0;
    const w = weights?.[d.key] ?? 0.25;
    return { ...d, norm, weight: w, contribution: norm * w };
  });
  const totalScore = route.score ?? contributions.reduce((s, c) => s + c.contribution, 0);

  return (
    <div className="glass rounded-2xl p-4 space-y-4 animate-fade-up">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className={`${rankStyles[rank] || rankStyles[2]} text-[11px] font-bold px-2.5 py-1 rounded-lg font-display`}>
            {rankLabels[rank] || `#${rank + 1}`}
          </span>
          <span className="text-[11px] text-slate-500 font-display">{route.category}</span>
        </div>
        <div className="text-right">
          <span className="text-lg font-bold text-white font-display">{totalScore.toFixed(3)}</span>
          <span className="text-[10px] text-slate-500 ml-1">score</span>
        </div>
      </div>

      {/* Summary */}
      <div className="flex items-center gap-4 text-[11px] text-slate-400 bg-white/[0.03] rounded-xl px-3 py-2 border border-white/[0.06]">
        <span>{formatDuration(route.time_min)}</span>
        <span>{formatCost(route.cost_est)}</span>
        <span>{route.transfers} transfer{route.transfers !== 1 ? 's' : ''}</span>
        <span className={`px-1.5 py-0.5 rounded-md text-[10px] font-semibold ring-1 ${riskBadgeClass(route.risk_crowding_cat)}`}>
          {route.risk_crowding_cat}
        </span>
      </div>

      {/* Normalized */}
      <div>
        <h4 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2 font-display">Normalized (0 = best, 1 = worst)</h4>
        <div className="space-y-2">
          {contributions.map(c => <ScoreBar key={c.key} value={c.norm} color={c.color} label={c.label} />)}
        </div>
      </div>

      {/* Weighted */}
      <div>
        <h4 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2 font-display">Weighted Contribution</h4>
        <div className="grid grid-cols-4 gap-2">
          {contributions.map(c => {
            const Icon = c.icon;
            return (
              <div key={c.key} className={`rounded-xl p-2.5 text-center ${c.lightBg} border border-white/[0.04]`}>
                <Icon size={15} className="mx-auto mb-1 text-slate-400" />
                <div className="text-[11px] font-bold text-white font-display">{c.contribution.toFixed(3)}</div>
                <div className="text-[9px] text-slate-500">{c.norm.toFixed(2)} x {c.weight.toFixed(2)}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Formula */}
      <div className="bg-white/[0.03] rounded-xl px-3 py-2 text-[11px] font-mono text-slate-500 overflow-x-auto border border-white/[0.06]">
        {contributions.map((c, i) => (
          <span key={c.key}>
            {i > 0 && ' + '}
            <span className="text-slate-300">{c.norm.toFixed(2)}</span>
            <span className="text-slate-600">x</span>
            <span className="text-slate-300">{c.weight.toFixed(2)}</span>
          </span>
        ))}
        {' = '}
        <span className="text-amber-400 font-bold">{totalScore.toFixed(3)}</span>
      </div>

      {route.explanation && (
        <p className="text-[11px] text-slate-500 italic">{route.explanation}</p>
      )}
    </div>
  );
}

export default function ScoringPage({ results, query }) {
  const navigate = useNavigate();
  const routes = results?.routes || [];
  const trip = results?.trip;
  const weights = trip
    ? { time: trip.wt_time, cost: trip.wt_cost, risk: trip.wt_risk, comfort: trip.wt_comfort }
    : { time: 0.25, cost: 0.25, risk: 0.25, comfort: 0.25 };

  if (!routes.length) {
    return (
      <div className="flex flex-col items-center justify-center px-4" style={{ minHeight: 'calc(100vh - 4rem)' }}>
        <div className="text-center animate-fade-up">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl glass mb-4">
            <BarChart3 size={28} className="text-slate-500" />
          </div>
          <h2 className="text-lg font-semibold text-slate-200 mb-1 font-display">No scoring data</h2>
          <p className="text-sm text-slate-500 mb-4">Search for routes first</p>
          <button onClick={() => navigate('/')} className="btn-primary py-2.5 px-5 rounded-xl text-sm font-display">
            Search Routes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 pt-4 pb-20 space-y-4">
      {/* Header */}
      <div className="animate-fade-up">
        <h1 className="text-xl font-bold text-white flex items-center gap-2 font-display">
          <BarChart3 size={20} className="text-amber-400" />
          Scoring Breakdown
        </h1>
        <p className="text-[11px] text-slate-500 mt-1 font-display">
          {query?.origin} <ArrowRight size={10} className="inline text-slate-600" /> {query?.destination}
        </p>
      </div>

      {/* How scoring works */}
      <div className="bg-amber-500/[0.06] border border-amber-500/15 rounded-2xl p-4 space-y-2 animate-fade-up delay-1">
        <div className="flex items-center gap-2">
          <Info size={15} className="text-amber-400 shrink-0" />
          <h3 className="text-sm font-semibold text-amber-200 font-display">How Scoring Works</h3>
        </div>
        <div className="text-[11px] text-amber-200/70 space-y-1.5">
          <p><strong className="text-amber-200">1. Normalize:</strong> Each metric scaled 0-1 across candidates. 0 = best, 1 = worst.</p>
          <p><strong className="text-amber-200">2. Risk</strong> = max(crowding, delay). <strong className="text-amber-200">Comfort</strong> = 60% walk + 40% transfers.</p>
          <p><strong className="text-amber-200">3. Weight:</strong> Multiply each by your chosen weight.</p>
          <p><strong className="text-amber-200">4. Sum:</strong> Add weighted values. <strong className="text-amber-200">Lower = better.</strong></p>
          <p><strong className="text-amber-200">5. Tie-break:</strong> risk &rarr; comfort &rarr; time &rarr; cost.</p>
        </div>
      </div>

      {/* Active weights */}
      <div className="glass rounded-2xl p-4 animate-fade-up delay-2">
        <h3 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-3 font-display">Active Weights</h3>
        <div className="grid grid-cols-4 gap-2">
          {DIMENSIONS.map(d => {
            const Icon = d.icon;
            const w = weights[d.key] ?? 0.25;
            return (
              <div key={d.key} className="text-center">
                <Icon size={17} className="mx-auto mb-1 text-slate-400" />
                <div className="text-sm font-bold text-white font-display">{w.toFixed(2)}</div>
                <div className="text-[10px] text-slate-500 font-display">{d.label}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Comparison table */}
      {routes.length > 1 && (
        <div className="glass rounded-2xl p-4 overflow-x-auto animate-fade-up delay-3">
          <h3 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-3 font-display">Route Comparison</h3>
          <table className="w-full text-[11px]">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="text-left py-2 pr-2 text-slate-500 font-medium font-display">Metric</th>
                {routes.map((_, i) => (
                  <th key={i} className="text-center py-2 px-2 text-slate-500 font-medium font-display">
                    {['Best', '2nd', '3rd'][i] || `#${i + 1}`}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-white/[0.04]">
                <td className="py-2 pr-2 text-slate-400">Time (Google)</td>
                {routes.map((r, i) => (
                  <td key={i} className="text-center py-2 px-2 font-mono text-slate-300">{formatDuration(r.time_min)}</td>
                ))}
              </tr>
              <tr className="border-b border-white/[0.04]">
                <td className="py-2 pr-2 text-slate-400">Realistic Time</td>
                {routes.map((r, i) => (
                  <td key={i} className={`text-center py-2 px-2 font-mono ${r.realistic_time_min > r.time_min ? 'text-amber-400 font-semibold' : 'text-slate-300'}`}>
                    {r.realistic_time_min != null ? formatDuration(r.realistic_time_min) : formatDuration(r.time_min)}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-white/[0.04]">
                <td className="py-2 pr-2 text-slate-400">Cost</td>
                {routes.map((r, i) => (
                  <td key={i} className="text-center py-2 px-2 font-mono text-slate-300">{formatCost(r.cost_est)}</td>
                ))}
              </tr>
              <tr className="border-b border-white/[0.04]">
                <td className="py-2 pr-2 text-slate-400">Crowding</td>
                {routes.map((r, i) => (
                  <td key={i} className="text-center py-2 px-2">
                    <span className={`px-1.5 py-0.5 rounded-md text-[10px] font-semibold ring-1 ${riskBadgeClass(r.risk_crowding_cat)}`}>
                      {r.risk_crowding_cat}
                    </span>
                  </td>
                ))}
              </tr>
              <tr className="border-b border-white/[0.04]">
                <td className="py-2 pr-2 text-slate-400">Delay</td>
                {routes.map((r, i) => (
                  <td key={i} className="text-center py-2 px-2">
                    <span className={`px-1.5 py-0.5 rounded-md text-[10px] font-semibold ring-1 ${riskBadgeClass(r.risk_delay_cat)}`}>
                      {r.risk_delay_cat}
                    </span>
                  </td>
                ))}
              </tr>
              <tr className="border-b border-white/[0.04]">
                <td className="py-2 pr-2 text-slate-400">Transfers</td>
                {routes.map((r, i) => (
                  <td key={i} className="text-center py-2 px-2 font-mono text-slate-300">{r.transfers}</td>
                ))}
              </tr>
              <tr className="bg-amber-500/5">
                <td className="py-2 pr-2 text-white font-semibold font-display">Score</td>
                {routes.map((r, i) => (
                  <td key={i} className="text-center py-2 px-2 font-mono font-bold text-amber-400">{r.score?.toFixed(3)}</td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Crowding Heatmaps */}
      {(() => {
        const stationNames = [];
        const seen = new Set();
        for (const route of routes) {
          for (const step of (route.steps || [])) {
            if (step.mode === 'Train' && step.from_name) {
              const name = step.from_name;
              if (!seen.has(name)) { seen.add(name); stationNames.push(name); }
            }
          }
        }
        if (!stationNames.length) return null;
        return (
          <div className="glass rounded-2xl p-4 space-y-3 animate-fade-up delay-4">
            <h3 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider font-display">Peak Hour Crowding</h3>
            <p className="text-[10px] text-slate-500">MRT crowding levels throughout the day</p>
            <div className="flex gap-3 mb-1 text-[9px] text-slate-500">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-emerald-500" /> Low</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-amber-500" /> Medium</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-red-500" /> High</span>
            </div>
            <div className="space-y-3">
              {stationNames.map((name, i) => <CrowdingHeatmap key={i} stationName={name} />)}
            </div>
          </div>
        );
      })()}

      {/* Detailed breakdowns */}
      <h3 className="text-sm font-semibold text-slate-200 pt-2 font-display">Detailed Breakdown</h3>
      {routes.map((route, i) => (
        <RouteScoreCard key={i} route={route} rank={i} weights={weights} />
      ))}
    </div>
  );
}
