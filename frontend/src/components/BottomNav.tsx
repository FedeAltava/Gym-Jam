import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, PlusCircle, History, User } from 'lucide-react';

const TABS = [
  { to: '/dashboard', label: 'Home', icon: LayoutDashboard },
  { to: '/workouts', label: 'Rutinas', icon: PlusCircle },
  { to: '/history', label: 'Historial', icon: History },
  { to: '/profile', label: 'Perfil', icon: User },
];

export function BottomNav() {
  const location = useLocation();

  return (
    <nav
      className="md:hidden fixed bottom-0 inset-x-0 z-30 flex bg-surface border-t border-border"
      style={{
        height: '60px',
        paddingBottom: 'env(safe-area-inset-bottom)',
      }}
    >
      {TABS.map(({ to, label, icon: Icon }) => {
        const active =
          location.pathname === to ||
          (to === '/dashboard' && location.pathname === '/');
        return (
          <Link
            key={to}
            to={to}
            className={[
              'flex-1 flex flex-col items-center justify-center gap-0.5 no-underline',
              'text-[11px] font-semibold',
              active ? 'text-accent' : 'text-muted',
            ].join(' ')}
          >
            <Icon size={22} strokeWidth={active ? 2.5 : 1.5} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
