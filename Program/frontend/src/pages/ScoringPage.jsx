import { useNavigate } from 'react-router-dom';
import { BarChart3, Clock, AlertTriangle, DollarSign, Heart, Info, ArrowRight } from 'lucide-react';
import { formatDuration, formatCost, riskBadgeClass } from '../utils/helpers';

const DIMENSIONS = [
  { key: 'time', normKey: 'normalized_time', label: 'Time', icon: Clock, color: 'bg-blue-500', lightColor: 'bg-blue-100' },
  { key: 'cost', normKey: 'normalized_cost', label: 'Cost', icon: DollarSign, color: 'bg-emerald-500', lightColor: 'bg-emerald-100' },
  { key: 'risk', normKey: 'normalized_risk', label: 'Risk', icon: AlertTriangle, color: 'bg-red-500', lightColor: 'bg-red-100' },
  { key: 'comfort', normKey: 'normalized_comfort', label: 'Comfort', icon: Heart, color: 'bg-purple-500', lightColor: 'bg-purple-100' },
];

function ScoreBar({ value, color, label }) {
  const pct = Math.round((value ?? 0) * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-slate-500 w-20 shrink-0">{label}</span>
      <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-600 w-10 text-right">{value?.toFixed(2) ?? '--'}</span>
    </div>
  );
}

function RouteScoreCard({ route, rank, weights }) {
  const rankLabels = ['Best', '2nd', '3rd'];
  const rankColors = ['bg-sky-500', 'bg-slate-400', 'bg-slate-300'];

  // Compute weighted contribution per dimension
  const contributions = DIMENSIONS.map(d => {
    const norm = route[d.normKey] ?? 0;
    const w = weights?.[d.key] ?? 0.25;
    return { ...d, norm, weight: w, contribution: norm * w };
  });
  const totalScore = route.score ?? contributions.reduce((s, c) => s + c.contribution, 0);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`${rankColors[rank] || rankColors[2]} text-white text-xs font-bold px-2.5 py-1 rounded-lg`}>
            {rankLabels[rank] || `#${rank + 1}`}
          </span>
          <span className="text-xs text-slate-500">{route.category}</span>
        </div>
        <div className="text-right">
          <span className="text-lg font-bold text-slate-800">{totalScore.toFixed(3)}</span>
          <span className="text-xs text-slate-400 ml-1">score</span>
        </div>
      </div>

      {/* Route summary */}
      <div className="flex items-center gap-4 text-xs text-slate-500 bg-slate-50 rounded-xl px-3 py-2">
        <span>{formatDuration(route.time_min)}</span>
        <span>{formatCost(route.cost_est)}</span>
        <span>{route.transfers} transfer{route.transfers !== 1 ? 's' : ''}</span>
        <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-semibold ${riskBadgeClass(route.risk_crowding_cat)}`}>
          Crowd: {route.risk_crowding_cat}
        </span>
      </div>

      {/* Normalized scores */}
      <div>
        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Normalized Scores (0 = best, 1 = worst)</h4>
        <div className="space-y-2">
          {contributions.map(c => (
            <ScoreBar key={c.key} value={c.norm} color={c.color} label={c.label} />
          ))}
        </div>
      </div>

      {/* Weighted breakdown */}
      <div>
        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Weighted Contribution</h4>
        <div className="grid grid-cols-4 gap-2">
          {contributions.map(c => {
            const Icon = c.icon;
            return (
              <div key={c.key} className={`rounded-xl p-2.5 text-center ${c.lightColor}`}>
                <Icon size={16} className="mx-auto mb-1 text-slate-600" />
                <div className="text-xs font-bold text-slate-800">{c.contribution.toFixed(3)}</div>
                <div className="text-[10px] text-slate-500">{c.norm.toFixed(2)} x {c.weight.toFixed(2)}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Formula line */}
      <div className="bg-slate-50 rounded-xl px-3 py-2 text-xs font-mono text-slate-500 overflow-x-auto">
        {contributions.map((c, i) => (
          <span key={c.key}>
            {i > 0 && ' + '}
            <span className="text-slate-700">{c.norm.toFixed(2)}</span>
            <span className="text-slate-400">x</span>
            <span className="text-slate-700">{c.weight.toFixed(2)}</span>
          </span>
        ))}
        {' = '}
        <span className="text-sky-600 font-bold">{totalScore.toFixed(3)}</span>
      </div>

      {/* Explanation */}
      {route.explanation && (
        <p className="text-xs text-slate-500 italic">{route.explanation}</p>
      )}
    </div>
  );
}

export default function ScoringPage({ results, query }) {
  const navigate = useNavigate();
  const routes = results?.routes || [];
  const trip = results?.trip;

  // Extract weights from the trip request
  const weights = trip
    ? { time: trip.wt_time, cost: trip.wt_cost, risk: trip.wt_risk, comfort: trip.wt_comfort }
    : { time: 0.25, cost: 0.25, risk: 0.25, comfort: 0.25 };

  if (!routes.length) {
    return (
      <div className="flex flex-col items-center justify-center px-4" style={{ minHeight: 'calc(100vh - 4rem)' }}>
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-100 mb-4">
            <BarChart3 size={28} className="text-slate-400" />
          </div>
          <h2 className="text-lg font-semibold text-slate-700 mb-1">No scoring data</h2>
          <p className="text-sm text-slate-500 mb-4">Search for routes first to see the scoring breakdown</p>
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
    <div className="px-4 pt-4 pb-6 space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <BarChart3 size={22} className="text-sky-500" />
          Scoring Breakdown
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          {query?.origin} <ArrowRight size={10} className="inline" /> {query?.destination}
        </p>
      </div>

      {/* How scoring works */}
      <div className="bg-sky-50 border border-sky-100 rounded-2xl p-4 space-y-2">
        <div className="flex items-center gap-2">
          <Info size={16} className="text-sky-500 shrink-0" />
          <h3 className="text-sm font-semibold text-sky-800">How Scoring Works</h3>
        </div>
        <div className="text-xs text-sky-700 space-y-1.5">
          <p><strong>1. Normalize:</strong> Each of the 4 metrics (time, cost, risk, comfort) is min-max scaled across all candidate routes. 0 = best, 1 = worst.</p>
          <p><strong>2. Risk</strong> = max(crowding, delay). <strong>Comfort</strong> = 60% walk time + 40% transfers. Both combine sub-metrics into one score.</p>
          <p><strong>3. Weight:</strong> Each normalized value is multiplied by your chosen weight (default 0.25 each).</p>
          <p><strong>4. Sum:</strong> The weighted values are added to produce the composite score. <strong>Lower = better.</strong></p>
          <p><strong>5. Tie-break:</strong> If scores are equal: risk &rarr; comfort &rarr; time &rarr; cost.</p>
        </div>
      </div>

      {/* Active weights */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4">
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Active Weights</h3>
        <div className="grid grid-cols-4 gap-2">
          {DIMENSIONS.map(d => {
            const Icon = d.icon;
            const w = weights[d.key] ?? 0.25;
            return (
              <div key={d.key} className="text-center">
                <Icon size={18} className="mx-auto mb-1 text-slate-500" />
                <div className="text-sm font-bold text-slate-800">{w.toFixed(2)}</div>
                <div className="text-[10px] text-slate-400">{d.label}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Comparison table */}
      {routes.length > 1 && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4 overflow-x-auto">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Route Comparison</h3>
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="text-left py-2 pr-2 text-slate-500 font-medium">Metric</th>
                {routes.map((_, i) => (
                  <th key={i} className="text-center py-2 px-2 text-slate-500 font-medium">
                    {['Best', '2nd', '3rd'][i] || `#${i + 1}`}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-slate-50">
                <td className="py-2 pr-2 text-slate-600">Time</td>
                {routes.map((r, i) => (
                  <td key={i} className="text-center py-2 px-2 font-mono">{formatDuration(r.time_min)}</td>
                ))}
              </tr>
              <tr className="border-b border-slate-50">
                <td className="py-2 pr-2 text-slate-600">Cost</td>
                {routes.map((r, i) => (
                  <td key={i} className="text-center py-2 px-2 font-mono">{formatCost(r.cost_est)}</td>
                ))}
              </tr>
              <tr className="border-b border-slate-50">
                <td className="py-2 pr-2 text-slate-600">Crowding</td>
                {routes.map((r, i) => (
                  <td key={i} className="text-center py-2 px-2">
                    <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-semibold ${riskBadgeClass(r.risk_crowding_cat)}`}>
                      {r.risk_crowding_cat}
                    </span>
                  </td>
                ))}
              </tr>
              <tr className="border-b border-slate-50">
                <td className="py-2 pr-2 text-slate-600">Delay</td>
                {routes.map((r, i) => (
                  <td key={i} className="text-center py-2 px-2">
                    <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-semibold ${riskBadgeClass(r.risk_delay_cat)}`}>
                      {r.risk_delay_cat}
                    </span>
                  </td>
                ))}
              </tr>
              <tr className="border-b border-slate-50">
                <td className="py-2 pr-2 text-slate-600">Transfers</td>
                {routes.map((r, i) => (
                  <td key={i} className="text-center py-2 px-2 font-mono">{r.transfers}</td>
                ))}
              </tr>
              <tr className="bg-sky-50/50">
                <td className="py-2 pr-2 text-slate-800 font-semibold">Score</td>
                {routes.map((r, i) => (
                  <td key={i} className="text-center py-2 px-2 font-mono font-bold text-sky-600">{r.score?.toFixed(3)}</td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Individual route breakdowns */}
      <h3 className="text-sm font-semibold text-slate-700 pt-2">Detailed Breakdown</h3>
      {routes.map((route, i) => (
        <RouteScoreCard key={i} route={route} rank={i} weights={weights} />
      ))}
    </div>
  );
}
