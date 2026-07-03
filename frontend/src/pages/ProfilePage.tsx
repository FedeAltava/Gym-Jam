import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, User } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { useAuthStore } from '../store/authStore';

export function ProfilePage() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [pwSuccess, setPwSuccess] = useState('');
  const [pwError, setPwError] = useState('');
  const [pwLoading, setPwLoading] = useState(false);

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    setPwSuccess('');
    setPwError('');

    if (newPassword !== confirmNewPassword) {
      setPwError('Las nuevas contraseñas no coinciden.');
      return;
    }

    setPwLoading(true);
    try {
      await apiFetch<void>('/auth/password', {
        method: 'PATCH',
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      setPwSuccess('Contraseña actualizada.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    } catch {
      setPwError('La contraseña actual es incorrecta.');
    } finally {
      setPwLoading(false);
    }
  }

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

      {/* Change password */}
      <div className="rounded-card border border-border bg-surface p-6 mt-6">
        <h2 className="font-bold mb-4 text-base text-text">Cambiar contraseña</h2>
        <form onSubmit={handleChangePassword} className="space-y-3">
          <div>
            <label
              htmlFor="current-password"
              className="block font-semibold mb-1 text-text text-sm"
            >
              Contraseña actual
            </label>
            <input
              id="current-password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full"
              style={{
                height: '44px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                padding: '0 12px',
                fontSize: '16px',
              }}
            />
          </div>
          <div>
            <label
              htmlFor="new-password"
              className="block font-semibold mb-1 text-text text-sm"
            >
              Nueva contraseña
            </label>
            <input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={8}
              className="w-full"
              style={{
                height: '44px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                padding: '0 12px',
                fontSize: '16px',
              }}
            />
          </div>
          <div>
            <label
              htmlFor="confirm-new-password"
              className="block font-semibold mb-1 text-text text-sm"
            >
              Confirmar nueva contraseña
            </label>
            <input
              id="confirm-new-password"
              type="password"
              value={confirmNewPassword}
              onChange={(e) => setConfirmNewPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full"
              style={{
                height: '44px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                padding: '0 12px',
                fontSize: '16px',
              }}
            />
          </div>

          {pwSuccess && <p className="text-xs text-accent">{pwSuccess}</p>}
          {pwError && <p className="text-xs text-danger">{pwError}</p>}

          <button
            type="submit"
            disabled={pwLoading}
            className="w-full font-semibold transition-all duration-200 disabled:opacity-60 rounded-btn bg-accent text-bg"
            style={{
              height: '48px',
              fontSize: '16px',
              border: 'none',
              cursor: 'pointer',
              marginTop: '4px',
            }}
          >
            {pwLoading ? 'Guardando…' : 'Actualizar contraseña'}
          </button>
        </form>
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
