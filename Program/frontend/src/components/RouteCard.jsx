import { Clock, DollarSign, Users, AlertTriangle, ChevronDown, ChevronUp, Footprints, Bus, TrainFront, Car, Ship, BarChart3, Receipt, CloudRain, Timer } from 'lucide-react';
import { useState } from 'react';
import RiskBadge from './RiskBadge';
import { formatDuration, formatCost, modeColor, isRainy } from '../utils/helpers';

const modeIcons = { Walk: Footprints, Bus: Bus, Train: TrainFront, Drive: Car, Tram: TrainFront, Ferry: Ship };

function StepIcon({ mode }) {
  const Icon = modeIcons[mode] || Footprints;
  return <Icon size={14} style={{ color: modeColor(mode) }} />;
}

const rankLabels = ['Best', '2nd', '3rd'];

export default function RouteCard({ route, rank, selected, onSelect, weights }) {
  const [expanded, setExpanded] = useState(false);

  const cb = route.cost_breakdown;
  const isTaxi = cb?.mode === 'taxi';
  const hasFreqWarning = route.steps?.some(s => s.bus_frequency?.frequency_cat === 'Low');

  return (
    <div
      onClick={() => onSelect?.(route)}
      className={`rounded-2xl p-3.5 transition-all duration-200 cursor-pointer border
        ${selected
          ? 'bg-amber-500/10 border-amber-500/30 shadow-lg shadow-amber-500/5'
          : 'bg-white/[0.04] border-white/[0.07] hover:bg-white/[0.06] hover:border-white/[0.1]'}`}
    >
      {/* Top row: rank + mode chain + score */}
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md font-display
          ${rank === 0 ? 'bg-amber-500/20 text-amber-400' : 'bg-white/[0.06] text-slate-400'}`}>
          {rankLabels[rank] || `#${rank + 1}`}
        </span>

        {/* Compact mode chain */}
        <div className="flex items-center gap-0.5 flex-1 min-w-0 overflow-hidden">
          {route.steps?.map((step, i) => (
            <div key={i} className="flex items-center gap-0.5 shrink-0">
              {i > 0 && <span className="text-slate-600 text-[8px]">&rsaquo;</span>}
              <StepIcon mode={step.mode} />
              {step.line_name && <span className="text-[10px] text-slate-400">{step.line_name}</span>}
            </div>
          ))}
        </div>

        <span className="text-[10px] font-mono text-slate-500 shrink-0">{route.score?.toFixed(2)}</span>
      </div>

      {/* Stats: time / cost / crowding / delay */}
      <div className="flex items-center gap-4 mb-1.5">
        <div className="flex items-center gap-1">
          <Clock size={12} className="text-slate-500" />
          <span className="text-[13px] font-bold text-white font-display">{formatDuration(route.time_min)}</span>
          {route.realistic_time_min != null && route.realistic_time_min > route.time_min && (
            <span className="text-[10px] text-amber-400">~{formatDuration(route.realistic_time_min)}</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <DollarSign size={12} className="text-slate-500" />
          <span className="text-[13px] font-bold text-white font-display">{formatCost(route.cost_est)}</span>
        </div>
        <div className="flex items-center gap-1.5 ml-auto">
          <RiskBadge category={route.risk_crowding_cat} />
          <RiskBadge category={route.risk_delay_cat} />
        </div>
      </div>

      {/* Inline warnings */}
      {isRainy(route.weather) && (
        <div className="flex items-center gap-1.5 text-[10px] text-blue-300 mb-1">
          <CloudRain size={11} /> Rain expected along route
        </div>
      )}
      {hasFreqWarning && (
        <div className="text-[10px] text-amber-300/80 mb-1">
          {route.steps.filter(s => s.bus_frequency?.frequency_cat === 'Low').map((s, i) => (
            <span key={i} className="flex items-center gap-1"><Timer size={10} /> Bus {s.line_name} every {s.bus_frequency.frequency_min}min</span>
          ))}
        </div>
      )}

      {/* Explanation */}
      {route.explanation && (
        <p className="text-[10px] text-slate-500 mb-1.5 leading-relaxed line-clamp-2">{route.explanation}</p>
      )}

      {/* Expand toggle */}
      <button onClick={e => { e.stopPropagation(); setExpanded(!expanded); }}
        className="flex items-center gap-1 text-[10px] text-amber-400/70 font-medium font-display hover:text-amber-300 transition-colors">
        {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        {expanded ? 'Less' : 'Details'}
      </button>

      {expanded && (
        <div className="mt-2.5 pt-2.5 border-t border-white/[0.06] space-y-3 anim-fade-in" onClick={e => e.stopPropagation()}>
          {/* Steps */}
          {route.steps?.map((step, i) => (
            <div key={i} className="flex items-start gap-2.5">
              <div className="mt-0.5 shrink-0"><StepIcon mode={step.mode} /></div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-[12px] font-medium text-slate-200 font-display">{step.mode}</span>
                  {step.line_name && (
                    <span className="text-[10px] bg-white/[0.06] px-1.5 py-0.5 rounded font-mono text-slate-400">{step.line_name}</span>
                  )}
                  {step.num_stops && <span className="text-[10px] text-slate-500">{step.num_stops} stops</span>}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">
                  {step.from_name && step.to_name && <span>{step.from_name} &rarr; {step.to_name}</span>}
                  {step.duration_min != null && <span className="ml-2">{formatDuration(step.duration_min)}</span>}
                </div>
                {(step.crowding || step.delay || step.bus_frequency) && (
                  <div className="flex gap-1.5 mt-1 flex-wrap">
                    {step.crowding && <RiskBadge category={step.crowding.category} label="crowd" />}
                    {step.delay && <RiskBadge category={step.delay.category} label="delay" />}
                    {step.bus_frequency && (
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold freq-${step.bus_frequency.frequency_cat.toLowerCase()}`}>
                        Every {step.bus_frequency.frequency_min}min
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Fare */}
          <div className="bg-white/[0.03] rounded-xl p-2.5 border border-white/[0.05]">
            <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider font-display flex items-center gap-1 mb-1.5">
              <Receipt size={10} /> Fare
            </h4>
            {cb && (
              <div className="space-y-0.5 text-[11px]">
                {isTaxi ? (
                  <>
                    <div className="flex justify-between"><span className="text-slate-400">Flag down</span><span className="font-mono text-slate-300">${cb.flag_down?.toFixed(2)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Distance ({cb.distance_km}km)</span><span className="font-mono text-slate-300">${cb.distance_charge?.toFixed(2)}</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Waiting</span><span className="font-mono text-slate-300">${cb.waiting_charge?.toFixed(2)}</span></div>
                    {cb.erp > 0 && (
                      <div className="flex justify-between text-amber-400"><span>ERP</span><span className="font-mono">${cb.erp?.toFixed(2)}</span></div>
                    )}
                  </>
                ) : (
                  <div className="flex justify-between"><span className="text-slate-400">Card fare ({cb.distance_km}km)</span><span className="font-mono text-slate-300">${cb.base_fare?.toFixed(2)}</span></div>
                )}
                <div className="flex justify-between pt-1 border-t border-white/[0.06] font-semibold">
                  <span className="text-slate-200 font-display">Total</span>
                  <span className="font-mono text-white">{formatCost(route.cost_est)}</span>
                </div>
              </div>
            )}
          </div>

          {/* Score mini-breakdown */}
          <div className="bg-white/[0.03] rounded-xl p-2.5 border border-white/[0.05]">
            <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider font-display flex items-center gap-1 mb-1.5">
              <BarChart3 size={10} /> Score
            </h4>
            <div className="grid grid-cols-4 gap-1.5 text-center">
              {[
                { k: 'normalized_time', l: 'Time', c: 'text-blue-400' },
                { k: 'normalized_cost', l: 'Cost', c: 'text-emerald-400' },
                { k: 'normalized_risk', l: 'Risk', c: 'text-red-400' },
                { k: 'normalized_comfort', l: 'Comfort', c: 'text-purple-400' },
              ].map(({ k, l, c }) => (
                <div key={k}>
                  <div className={`text-[12px] font-bold font-display ${c}`}>{(route[k] ?? 0).toFixed(2)}</div>
                  <div className="text-[9px] text-slate-500">{l}</div>
                </div>
              ))}
            </div>
            <div className="text-center mt-1.5 pt-1 border-t border-white/[0.05]">
              <span className="text-[13px] font-bold text-amber-400 font-display">{route.score?.toFixed(3)}</span>
              <span className="text-[9px] text-slate-500 ml-1">composite</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
