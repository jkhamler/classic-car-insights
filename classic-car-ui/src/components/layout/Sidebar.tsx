import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Search, Car, TrendingUp, Bell, FileText } from 'lucide-react';
import clsx from 'clsx';

const links = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/listings', icon: Search, label: 'Listings' },
  { to: '/vehicles', icon: Car, label: 'Vehicles' },
  { to: '/trends', icon: TrendingUp, label: 'Trends' },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
  { to: '/reports', icon: FileText, label: 'Reports' },
];

export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-10 flex w-56 flex-col bg-slate-900">
      <div className="flex h-16 items-center gap-2 px-5">
        <Car className="h-6 w-6 text-emerald-400" />
        <span className="text-lg font-bold text-white">CCI</span>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-slate-800 px-5 py-4">
        <p className="text-xs text-slate-500">Classic Car Insights</p>
      </div>
    </aside>
  );
}
