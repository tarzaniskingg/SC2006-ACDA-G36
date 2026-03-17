import { NavLink } from 'react-router-dom';
import { Search, Route, Map, BarChart3, Settings } from 'lucide-react';

const tabs = [
  { to: '/', icon: Search, label: 'Search' },
  { to: '/results', icon: Route, label: 'Routes' },
  { to: '/map', icon: Map, label: 'Map' },
  { to: '/scoring', icon: BarChart3, label: 'Scoring' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function BottomNav() {
  return (
    <nav className="shrink-0 bg-white/80 backdrop-blur-lg border-t border-slate-200">
      <div className="max-w-lg mx-auto flex justify-around items-center h-16">
        {tabs.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 px-2 py-1 text-xs font-medium transition-colors
               ${isActive ? 'text-sky-500' : 'text-slate-400'}`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={20} strokeWidth={isActive ? 2.5 : 1.8} />
                <span>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
