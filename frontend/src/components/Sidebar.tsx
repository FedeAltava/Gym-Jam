import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../lib/api';
import { LayoutDashboard, PlusCircle, History, LogOut, User } from 'lucide-react';

const NAV = [
  { to: '/dashboard', label: 'Home', icon: LayoutDashboard },
  { to: '/workouts', label: 'Rutinas', icon: PlusCircle },
  { to: '/history', label: 'Historial', icon: History },
  { to: '/profile', label: 'Perfil', icon: User },
];

export function Sidebar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <aside className="hidden md:flex flex-col w-60 fixed inset-y-0 left-0 z-30 bg-surface border-r border-border">
      {/* Logo */}
      <div className="flex items-center px-6 border-b border-border" style={{ height: '56px' }}>
        <Link to="/dashboard" className="text-lg font-bold tracking-tight no-underline">
          <span className="text-text">Gym</span>
          <span className="text-accent">Jam</span>
        </Link>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ to, label, icon: Icon }) => {
          const active =
            location.pathname === to ||
            (to === '/dashboard' && location.pathname === '/');
          return (
            <Link
              key={to}
              to={to}
              className={[
                'flex items-center gap-3 px-3 py-2.5 rounded-btn text-sm font-semibold transition-colors no-underline',
                active
                  ? 'bg-[var(--accent-soft)] text-accent'
                  : 'bg-transparent text-muted hover:text-text',
              ].join(' ')}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="px-3 py-4 border-t border-border">
        <div className="flex items-center gap-3 px-3 py-2 mb-1">
          <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-elevated">
            <User size={16} className="text-muted" />
          </div>
          <p className="text-xs truncate flex-1 text-muted">{user?.email}</p>
        </div>
        <button
          onClick={() => {
            void (async () => {
              try {
                await apiFetch<void>('/auth/logout', { method: 'POST' });
              } catch {
                // ignore — local logout happens regardless
              }
              logout();
              navigate('/login');
            })();
          }}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-btn text-sm font-semibold transition-colors text-muted hover:text-danger"
          style={{ backgroundColor: 'transparent' }}
        >
          <LogOut size={18} />
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
