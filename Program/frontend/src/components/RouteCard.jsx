import { Clock, DollarSign, Users, AlertTriangle, ChevronDown, ChevronUp, Footprints, Bus, TrainFront, Car, Ship, BarChart3, Receipt, CloudRain, Timer } from 'lucide-react';
import { useState } from 'react';
import RiskBadge from './RiskBadge';
import { formatDuration, formatCost, modeColor, frequencyBadgeClass, isRainy } from '../utils/helpers';

const modeIcons = {
  Walk: Footprints,
  Bus: Bus,
  Train: TrainFront,
  Drive: Car,
  Tram: TrainFront,
  Ferry: Ship,
};

function StepIcon({ mode }) {
  const Icon = modeIcons[mode] || Footprints;
  return <Icon size={16} style={{ color: modeColor(mode) }} />;
}

function ScoreBar({ value, color, label, weight, contribution }) {
  const pct = Math.round((value ?? 0) * 100);
  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-slate-500">{label}</span>
        <span className="text-[11px] font-mono text-slate-400">
          {value?.toFixed(2)} x {weight?.toFixed(2)} = <span className="text-slate-600 font-semibold">{contribution?.toFixed(3)}</span>
        </span>
      </div>
      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function RouteCard({ route, rank, selected, onSelect, weights }) {
  const [expanded, setExpanded] = useState(false);

  const rankLabels = ['Best', '2nd', '3rd'];
  const rankColors = ['bg-sky-500', 'bg-slate-400', 'bg-slate-300'];

  // Score attribution (4 dimensions: time, cost, risk, comfort)
  const w = weights || { time: 0.25, cost: 0.25, risk: 0.25, comfort: 0.25 };
  const dims = [
    { key: 'time', normKey: 'normalized_time', label: 'Time', color: 'bg-blue-500', weight: w.time },
    { key: 'cost', normKey: 'normalized_cost', label: 'Cost', color: 'bg-emerald-500', weight: w.cost },
    { key: 'risk', normKey: 'normalized_risk', label: 'Risk', sub: 'crowd+delay', color: 'bg-red-500', weight: w.risk },
    { key: 'comfort', normKey: 'normalized_comfort', label: 'Comfort', sub: 'walk+transfers', color: 'bg-purple-500', weight: w.comfort },
  ];

  const cb = route.cost_breakdown;
  const isTaxi = cb?.mode === 'taxi';

  return (
    <div
      onClick={() => onSelect?.(route)}
      className={`bg-white rounded-2xl shadow-sm border-2 p-4 transition-all duration-200 cursor-pointer
        ${selected ? 'border-sky-500 shadow-md' : 'border-slate-100 hover:border-slate-200'}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`${rankColors[rank] || rankColors[2]} text-white text-xs font-bold px-2.5 py-1 rounded-lg`}>
            {rankLabels[rank] || `#${rank + 1}`}
          </span>
          <span className="text-xs text-slate-400 font-medium">{route.category}</span>
        </div>
        {route.score != null && (
          <span className="text-xs font-mono text-slate-400">
            {route.score.toFixed(2)}
          </span>
        )}
      </div>

      {/* Mode chain preview */}
      {route.steps?.length > 0 && (
        <div className="flex items-center gap-1 mb-3 overflow-x-auto pb-1">
          {route.steps.map((step, i) => (
            <div key={i} className="flex items-center gap-1">
              {i > 0 && <span className="text-slate-300 text-xs">{'>'}</span>}
              <div className="flex items-center gap-1 bg-slate-50 rounded-lg px-2 py-1">
                <StepIcon mode={step.mode} />
                <span className="text-xs font-medium text-slate-600 whitespace-nowrap">
                  {step.line_name || step.mode}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        <div className="flex items-center gap-1.5">
          <Clock size={14} className="text-slate-400" />
          <div className="flex flex-col">
            <span className="text-sm font-semibold">{formatDuration(route.time_min)}</span>
            {route.realistic_time_min != null && route.realistic_time_min > route.time_min && (
              <span className="text-[10px] text-amber-600 font-medium">~{formatDuration(route.realistic_time_min)}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <DollarSign size={14} className="text-slate-400" />
          <span className="text-sm font-semibold">{formatCost(route.cost_est)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Users size={14} className="text-slate-400" />
          <RiskBadge category={route.risk_crowding_cat} />
        </div>
        <div className="flex items-center gap-1.5">
          <AlertTriangle size={14} className="text-slate-400" />
          <RiskBadge category={route.risk_delay_cat} />
        </div>
      </div>

      {/* Weather badge (Feature 2) */}
      {isRainy(route.weather) && (
        <div className="flex items-center gap-1.5 mb-2 bg-blue-50 border border-blue-100 rounded-lg px-2.5 py-1.5">
          <CloudRain size={14} className="text-blue-500" />
          <span className="text-xs text-blue-700 font-medium">Rain expected along route — allow extra time for walking segments</span>
        </div>
      )}

      {/* Bus frequency warnings (Feature 5) */}
      {route.steps?.some(s => s.bus_frequency && s.bus_frequency.frequency_cat === 'Low') && (
        <div className="bg-amber-50 border border-amber-100 rounded-lg px-2.5 py-1.5 mb-2">
          {route.steps.filter(s => s.bus_frequency && s.bus_frequency.frequency_cat === 'Low').map((s, i) => (
            <div key={i} className="flex items-center gap-1.5 text-xs text-amber-700">
              <Timer size={12} className="shrink-0" />
              <span>Bus {s.line_name} runs every {s.bus_frequency.frequency_min} min. Missing it adds ~{s.bus_frequency.miss_penalty_min} min.</span>
            </div>
          ))}
        </div>
      )}

      {/* Explanation */}
      {route.explanation && (
        <p className="text-xs text-slate-500 mb-3 leading-relaxed">{route.explanation}</p>
      )}

      {/* Expand toggle */}
      <button
        onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
        className="flex items-center gap-1 text-xs text-sky-500 font-medium"
      >
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {expanded ? 'Hide' : 'View'} details
      </button>

      {/* Expanded section */}
      {expanded && (
        <div className="mt-3 border-t border-slate-100 pt-3 space-y-4" onClick={e => e.stopPropagation()}>

          {/* Step-by-step directions */}
          {route.steps && (
            <div className="space-y-2.5">
              <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide flex items-center gap-1.5">
                Route Steps
              </h4>
              {route.steps.map((step, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="mt-0.5 shrink-0">
                    <StepIcon mode={step.mode} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium">{step.mode}</span>
                      {step.line_name && (
                        <span className="text-xs bg-slate-100 px-1.5 py-0.5 rounded font-mono">
                          {step.line_name}
                        </span>
                      )}
                      {step.num_stops && (
                        <span className="text-xs text-slate-400">{step.num_stops} stops</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-0.5 flex-wrap">
                      {step.duration_min != null && (
                        <span className="text-xs text-slate-400">{formatDuration(step.duration_min)}</span>
                      )}
                      {step.from_name && step.to_name && (
                        <span className="text-xs text-slate-400 truncate">
                          {step.from_name} &rarr; {step.to_name}
                        </span>
                      )}
                    </div>
                    {step.departure_time && (
                      <span className="text-xs text-slate-400">Depart: {step.departure_time}</span>
                    )}
                    {(step.crowding || step.delay || step.bus_frequency) && (
                      <div className="flex gap-2 mt-1 flex-wrap">
                        {step.crowding && <RiskBadge category={step.crowding.category} label="crowd" />}
                        {step.delay && <RiskBadge category={step.delay.category} label="delay" />}
                        {step.bus_frequency && (
                          <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-semibold ${frequencyBadgeClass(step.bus_frequency.frequency_cat)}`}>
                            Every {step.bus_frequency.frequency_min} min
                          </span>
                        )}
                        {step.bus_frequency?.next_arrival_min != null && (
                          <span className="text-[10px] text-sky-600 font-medium">
                            Next: {step.bus_frequency.next_arrival_min} min
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Score Attribution */}
          {route.score != null && (
            <div className="bg-slate-50 rounded-xl p-3 space-y-2">
              <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide flex items-center gap-1.5">
                <BarChart3 size={12} />
                Score Breakdown
              </h4>
              <div className="space-y-1.5">
                {dims.map(d => {
                  const norm = route[d.normKey] ?? 0;
                  const contribution = norm * d.weight;
                  return (
                    <ScoreBar
                      key={d.key}
                      value={norm}
                      color={d.color}
                      label={d.label}
                      weight={d.weight}
                      contribution={contribution}
                    />
                  );
                })}
              </div>
              <div className="flex items-center justify-between pt-1 border-t border-slate-200">
                <span className="text-[11px] text-slate-500">Composite Score</span>
                <span className="text-sm font-bold text-sky-600">{route.score.toFixed(3)}</span>
              </div>
              <p className="text-[10px] text-slate-400">Lower is better. 0 = best possible, 1 = worst.</p>
            </div>
          )}

          {/* Cost Breakdown */}
          <div className="bg-slate-50 rounded-xl p-3 space-y-2">
            <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide flex items-center gap-1.5">
              <Receipt size={12} />
              Fare Breakdown
            </h4>
            {cb ? (
              <div className="space-y-1">
                {isTaxi ? (
                  <>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Flag down</span>
                      <span className="font-mono text-slate-700">${cb.flag_down?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Metered distance ({cb.distance_km} km)</span>
                      <span className="font-mono text-slate-700">${cb.distance_charge?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Waiting / slow traffic</span>
                      <span className="font-mono text-slate-700">${cb.waiting_charge?.toFixed(2)}</span>
                    </div>
                    {cb.erp != null && cb.erp > 0 && (
                      <>
                        <div className="flex justify-between text-xs text-orange-600 font-medium">
                          <span>ERP charges</span>
                          <span className="font-mono">${cb.erp?.toFixed(2)}</span>
                        </div>
                        {cb.erp_gantries?.map((g, i) => (
                          <div key={i} className="flex justify-between text-[10px] text-slate-400 pl-2">
                            <span>{g.name}</span>
                            <span className="font-mono">${g.charge?.toFixed(2)}</span>
                          </div>
                        ))}
                      </>
                    )}
                  </>
                ) : (
                  <>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Adult card fare ({cb.distance_km} km)</span>
                      <span className="font-mono text-slate-700">${cb.base_fare?.toFixed(2)}</span>
                    </div>
                  </>
                )}
                <div className="flex justify-between text-xs pt-1 border-t border-slate-200">
                  <span className="text-slate-700 font-semibold">Total</span>
                  <span className="font-mono font-bold text-slate-800">{formatCost(route.cost_est)}</span>
                </div>
                <p className="text-[10px] text-slate-400">
                  {isTaxi
                    ? `ComfortDelGro metered rate${cb.erp ? ' + ERP' : ''}. Excludes peak/midnight surcharges and booking fees.`
                    : 'TransitLink adult card fare (distance-based). Includes bus-MRT transfers within 45 min.'}
                </p>
              </div>
            ) : (
              <div className="text-xs text-slate-500">
                <span className="font-semibold">{formatCost(route.cost_est)}</span> estimated
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}
