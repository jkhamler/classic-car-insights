import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Search, Car, TrendingUp, Bell, FileText, Menu, X } from 'lucide-react';
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
  const [open, setOpen] = useState(false);

  return (
    <>
      <div className="sticky top-0 z-20 flex h-14 items-center justify-between bg-slate-900 px-4 md:hidden">
        <div className="flex items-center gap-2">
          <Car className="h-5 w-5 text-emerald-400" />
          <span className="text-base font-bold text-white">CCI</span>
        </div>
        <button
          onClick={() => setOpen(true)}
          aria-label="Open menu"
          className="rounded-lg p-2 text-slate-300 hover:bg-slate-800 hover:text-white"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>

      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-slate-900 transition-transform duration-200 ease-in-out',
          'md:w-56 md:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between gap-2 px-5">
          <div className="flex items-center gap-2">
            <Car className="h-6 w-6 text-emerald-400" />
            <span className="text-lg font-bold text-white">CCI</span>
          </div>
          <button
            onClick={() => setOpen(false)}
            aria-label="Close menu"
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white md:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {links.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setOpen(false)}
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
    </>
  );
}
