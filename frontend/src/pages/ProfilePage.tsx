import { useNavigate } from 'react-router-dom';
import { LogOut, User } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { useAuthStore } from '../store/authStore';

export function ProfilePage() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  async function handleLogout() {
    // Best-effort server-side revocation of the refresh token; local logout
    // must happen regardless of the outcome. The refresh token is read from
    // the store AT SEND TIME so a rotation that happened in between (another
    // tab, background refresh) cannot leave a stale token in the request.
    // Legacy sessions (persisted before refresh tokens existed) have none —
    // skip the server call entirely instead of POSTing refresh_token: null,
    // which the backend treats as a revoke-all request.
    const refreshToken = useAuthStore.getState().refreshToken;
    if (refreshToken) {
      try {
        await apiFetch<void>('/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch {
        // Ignore errors — the session is cleared locally anyway.
      }
    }
    logout();
    navigate('/login');
  }

  return (
    <div className="max-w-sm">
      <h1 className="font-bold mb-6 text-text" style={{ fontSize: '24px' }}>
        Mi Perfil
      </h1>

      <div className="rounded-card border border-border bg-surface p-6 space-y-4">
        {/* Avatar */}
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-elevated flex items-center justify-center shrink-0">
            <User size={28} className="text-muted" />
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-text truncate">{user?.email}</p>
            <p className="text-xs text-muted mt-0.5">
              Miembro desde{' '}
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString('es', {
                    year: 'numeric',
                    month: 'long',
                  })
                : '—'}
            </p>
          </div>
        </div>

        <hr className="border-border" />

        {/* Email row */}
        <div>
          <p className="text-xs text-muted mb-1">Email</p>
          <p className="text-sm text-text">{user?.email}</p>
        </div>
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="mt-6 w-full flex items-center justify-center gap-2 font-semibold rounded-btn border border-border text-muted transition-colors hover:text-danger hover:border-danger"
        style={{ height: '48px', backgroundColor: 'transparent', cursor: 'pointer' }}
      >
        <LogOut size={18} />
        Cerrar sesión
      </button>
    </div>
  );
}
