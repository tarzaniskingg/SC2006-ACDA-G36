import { formatDuration, formatCost } from '../utils/helpers';

function cellColor(value, allValues, lowerBetter = true) {
  if (allValues.length < 2 || value == null) return '';
  const valid = allValues.filter(v => v != null);
  if (valid.length < 2) return '';
  const sorted = [...valid].sort((a, b) => a - b);
  const best = lowerBetter ? sorted[0] : sorted[sorted.length - 1];
  const worst = lowerBetter ? sorted[sorted.length - 1] : sorted[0];
  if (value === best) return 'bg-emerald-500/10 text-emerald-400 font-semibold';
  if (value === worst) return 'bg-red-500/10 text-red-400';
  return '';
}

// Parse "Morning Rush: 07:30" into { group: "Morning Rush", label: "07:30" }
function parseSlotLabel(time) {
  const idx = time.indexOf(': ');
  if (idx === -1) return { group: '', label: time };
  return { group: time.slice(0, idx), label: time.slice(idx + 2) };
}

function GroupTable({ groupName, slots }) {
  if (!slots.length) return null;

  const allScores = slots.map(s => s.best_score);
  const allTimes = slots.map(s => s.routes?.[0]?.time_min);
  const allReal = slots.map(s => s.routes?.[0]?.realistic_time_min);
  const allCosts = slots.map(s => s.routes?.[0]?.cost_est);

  return (
    <div className="space-y-2">
      <h4 className="text-[12px] font-semibold text-amber-400 font-display">{groupName}</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="border-b border-white/[0.06]">
              <th className="text-left py-1.5 pr-2 text-slate-500 font-medium font-display w-20">Metric</th>
              {slots.map((s, i) => (
                <th key={i} className="text-center py-1.5 px-1.5 text-slate-400 font-medium font-display whitespace-nowrap">
                  {parseSlotLabel(s.time).label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-white/[0.04]">
              <td className="py-1.5 pr-2 text-slate-400">Score</td>
              {slots.map((s, i) => (
                <td key={i} className={`text-center py-1.5 px-1.5 font-mono rounded ${cellColor(s.best_score, allScores)}`}>
                  {s.best_score?.toFixed(3) ?? '--'}
                </td>
              ))}
            </tr>
            <tr className="border-b border-white/[0.04]">
              <td className="py-1.5 pr-2 text-slate-400">Time</td>
              {slots.map((s, i) => {
                const t = s.routes?.[0]?.time_min;
                return (
                  <td key={i} className={`text-center py-1.5 px-1.5 font-mono rounded ${cellColor(t, allTimes)}`}>
                    {t != null ? formatDuration(t) : '--'}
                  </td>
                );
              })}
            </tr>
            <tr className="border-b border-white/[0.04]">
              <td className="py-1.5 pr-2 text-slate-400">Realistic</td>
              {slots.map((s, i) => {
                const t = s.routes?.[0]?.realistic_time_min;
                return (
                  <td key={i} className={`text-center py-1.5 px-1.5 font-mono rounded ${cellColor(t, allReal)}`}>
                    {t != null ? formatDuration(t) : '--'}
                  </td>
                );
              })}
            </tr>
            <tr className="border-b border-white/[0.04]">
              <td className="py-1.5 pr-2 text-slate-400">Cost</td>
              {slots.map((s, i) => {
                const c = s.routes?.[0]?.cost_est;
                return (
                  <td key={i} className={`text-center py-1.5 px-1.5 font-mono rounded ${cellColor(c, allCosts)}`}>
                    {c != null ? formatCost(c) : '--'}
                  </td>
                );
              })}
            </tr>
            <tr>
              <td className="py-1.5 pr-2 text-slate-400">Crowding</td>
              {slots.map((s, i) => {
                const cat = s.routes?.[0]?.risk_crowding_cat;
                const cls = { Low: 'risk-low', Medium: 'risk-med', High: 'risk-high' }[cat] || 'risk-unk';
                return (
                  <td key={i} className="text-center py-1.5 px-1.5">
                    {cat ? <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${cls}`}>{cat}</span> : '--'}
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function TimeCompare({ data, onClose }) {
  if (!data?.slots?.length) return null;

  // Group slots by their group prefix
  const groups = [];
  let currentGroup = null;
  for (const slot of data.slots) {
    const { group } = parseSlotLabel(slot.time);
    if (!currentGroup || currentGroup.name !== group) {
      currentGroup = { name: group, slots: [] };
      groups.push(currentGroup);
    }
    currentGroup.slots.push(slot);
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-end sm:items-center justify-center"
      style={{ backdropFilter: 'blur(8px)' }}
      onClick={onClose}>
      <div className="w-full max-w-lg max-h-[85vh] overflow-y-auto p-4 space-y-4 rounded-t-2xl sm:rounded-2xl border border-white/[0.08]"
        style={{ background: 'rgba(12, 16, 28, 0.97)' }}
        onClick={e => e.stopPropagation()}>

        <div className="flex items-center justify-between">
          <h3 className="text-[14px] font-bold text-white font-display">Departure Time Comparison</h3>
          <button onClick={onClose}
            className="text-[11px] text-slate-400 hover:text-slate-200 font-medium px-2 py-1 rounded-lg hover:bg-white/[0.05] transition-colors">
            Close
          </button>
        </div>

        <p className="text-[10px] text-slate-500 font-display -mt-2">
          {data.origin} &rarr; {data.destination}
        </p>

        {groups.map((g, i) => (
          <GroupTable key={i} groupName={g.name} slots={g.slots} />
        ))}

        <p className="text-[9px] text-slate-500 text-center font-display pt-1">
          Best route per time slot &middot; Lower score is better &middot; All times are future departures
        </p>
      </div>
    </div>
  );
}
