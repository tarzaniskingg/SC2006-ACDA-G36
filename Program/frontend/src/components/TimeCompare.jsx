import { formatDuration, formatCost, riskBadgeClass } from '../utils/helpers';

function cellColor(value, allValues, lowerBetter = true) {
  if (allValues.length < 2 || value == null) return '';
  const sorted = [...allValues].filter(v => v != null).sort((a, b) => a - b);
  if (sorted.length < 2) return '';
  const best = lowerBetter ? sorted[0] : sorted[sorted.length - 1];
  const worst = lowerBetter ? sorted[sorted.length - 1] : sorted[0];
  if (value === best) return 'bg-emerald-50 text-emerald-700 font-semibold';
  if (value === worst) return 'bg-red-50 text-red-700';
  return 'bg-amber-50 text-amber-700';
}

export default function TimeCompare({ data, onClose }) {
  if (!data?.slots?.length) return null;

  const slots = data.slots;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-end sm:items-center justify-center">
      <div className="bg-white rounded-t-2xl sm:rounded-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-800">Departure Time Comparison</h3>
          <button onClick={onClose} className="text-xs text-slate-400 hover:text-slate-600 font-medium px-2 py-1">
            Close
          </button>
        </div>

        <p className="text-[10px] text-slate-400">
          {data.origin} &rarr; {data.destination}
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="text-left py-2 pr-2 text-slate-500 font-medium">Metric</th>
                {slots.map((s, i) => (
                  <th key={i} className="text-center py-2 px-2 text-slate-500 font-medium whitespace-nowrap">
                    {s.time}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Best score */}
              <tr className="border-b border-slate-50">
                <td className="py-2 pr-2 text-slate-600">Score</td>
                {slots.map((s, i) => {
                  const scores = slots.map(sl => sl.best_score).filter(v => v != null);
                  return (
                    <td key={i} className={`text-center py-2 px-2 font-mono ${cellColor(s.best_score, scores)}`}>
                      {s.best_score?.toFixed(3) ?? '--'}
                    </td>
                  );
                })}
              </tr>
              {/* Time */}
              <tr className="border-b border-slate-50">
                <td className="py-2 pr-2 text-slate-600">Time</td>
                {slots.map((s, i) => {
                  const t = s.routes?.[0]?.time_min;
                  const all = slots.map(sl => sl.routes?.[0]?.time_min);
                  return (
                    <td key={i} className={`text-center py-2 px-2 font-mono ${cellColor(t, all)}`}>
                      {t != null ? formatDuration(t) : '--'}
                    </td>
                  );
                })}
              </tr>
              {/* Realistic time */}
              <tr className="border-b border-slate-50">
                <td className="py-2 pr-2 text-slate-600">Realistic</td>
                {slots.map((s, i) => {
                  const t = s.routes?.[0]?.realistic_time_min;
                  const all = slots.map(sl => sl.routes?.[0]?.realistic_time_min);
                  return (
                    <td key={i} className={`text-center py-2 px-2 font-mono ${cellColor(t, all)}`}>
                      {t != null ? formatDuration(t) : '--'}
                    </td>
                  );
                })}
              </tr>
              {/* Cost */}
              <tr className="border-b border-slate-50">
                <td className="py-2 pr-2 text-slate-600">Cost</td>
                {slots.map((s, i) => {
                  const c = s.routes?.[0]?.cost_est;
                  const all = slots.map(sl => sl.routes?.[0]?.cost_est);
                  return (
                    <td key={i} className={`text-center py-2 px-2 font-mono ${cellColor(c, all)}`}>
                      {c != null ? formatCost(c) : '--'}
                    </td>
                  );
                })}
              </tr>
              {/* Crowding */}
              <tr className="border-b border-slate-50">
                <td className="py-2 pr-2 text-slate-600">Crowding</td>
                {slots.map((s, i) => {
                  const cat = s.routes?.[0]?.risk_crowding_cat;
                  return (
                    <td key={i} className="text-center py-2 px-2">
                      {cat ? (
                        <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-semibold ${riskBadgeClass(cat)}`}>
                          {cat}
                        </span>
                      ) : '--'}
                    </td>
                  );
                })}
              </tr>
            </tbody>
          </table>
        </div>

        <p className="text-[10px] text-slate-400 text-center">
          Showing best route per time slot. Lower score is better.
        </p>
      </div>
    </div>
  );
}
