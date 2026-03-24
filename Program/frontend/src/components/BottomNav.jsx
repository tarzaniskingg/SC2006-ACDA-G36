import { NavLink } from 'react-router-dom';
import { MapPin, BarChart3, Settings } from 'lucide-react';

const tabs = [
  { to: '/', icon: MapPin, label: 'Explore' },
  { to: '/scoring', icon: BarChart3, label: 'Scoring' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function BottomNav({ hasResults }) {
  return (
    <nav className="shrink-0 relative z-30 border-t border-white/[0.06] panel">
      <div className="max-w-lg mx-auto flex justify-around items-center h-14">
        {tabs.map(({ to, icon: Icon, label }) => {
          if (to === '/scoring' && !hasResults) return (
            <div key={to} className="flex flex-col items-center gap-0.5 px-3 py-1.5 text-[10px] font-medium text-slate-600 font-display cursor-not-allowed">
              <Icon size={19} strokeWidth={1.5} />
              <span>{label}</span>
            </div>
          );
          return (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl text-[10px] font-medium transition-all duration-150 font-display
                 ${isActive ? 'text-amber-400' : 'text-slate-500 hover:text-slate-300'}`
              }>
              {({ isActive }) => (
                <>
                  <Icon size={19} strokeWidth={isActive ? 2.2 : 1.5} />
                  <span>{label}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}
