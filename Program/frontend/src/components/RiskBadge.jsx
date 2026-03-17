import { riskBadgeClass, riskLabel } from '../utils/helpers';

export default function RiskBadge({ category, label }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${riskBadgeClass(category)}`}>
      {label && <span className="text-[10px] uppercase tracking-wide opacity-70">{label}</span>}
      {riskLabel(category)}
    </span>
  );
}
