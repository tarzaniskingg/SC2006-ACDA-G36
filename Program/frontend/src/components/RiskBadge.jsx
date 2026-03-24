import { riskLabel } from '../utils/helpers';

export default function RiskBadge({ category, label }) {
  const cls = {
    Low: 'risk-low',
    Medium: 'risk-med',
    High: 'risk-high',
  }[category] || 'risk-unk';

  return (
    <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold ${cls}`}>
      {label && <span className="text-[8px] uppercase tracking-wide opacity-60">{label}</span>}
      {riskLabel(category)}
    </span>
  );
}
