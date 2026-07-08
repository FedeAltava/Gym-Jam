import { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, User } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { useAuthStore } from '../store/authStore';
import { useUserStats } from '../hooks/useStats';
import { useUserPreferences, useUpdatePreferences } from '../hooks/useUserPreferences';
import { Spinner } from '../components/Spinner';

// ---------------------------------------------------------------------------
// StatTile
// ---------------------------------------------------------------------------

interface StatTileProps {
  value: number | undefined;
  label: string;
}

function StatTile({ value, label }: StatTileProps) {
  return (
    <div className="flex-1 flex flex-col items-center py-4 px-2">
      <span className="font-condensed font-bold text-3xl text-text leading-none">
        {value ?? '—'}
      </span>
      <span className="text-xs text-muted mt-1 text-center">{label}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ProfilePage
// ---------------------------------------------------------------------------

export function ProfilePage() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const { data: stats, isLoading: statsLoading } = useUserStats();
  const { data: prefs, isLoading: prefsLoading } = useUserPreferences();
  const updatePrefs = useUpdatePreferences();

  // Derive display name from email (before the @)
  const displayName = user?.email
    ? user.email.split('@')[0].replace(/[._-]/g, ' ')
    : '';

  // ------------- Rest timer edit state -------------
  const [editingRest, setEditingRest] = useState(false);
  const [restInput, setRestInput] = useState<string>('');
  const restInputRef = useRef<HTMLInputElement>(null);

  function startEditRest() {
    setRestInput(String(prefs?.rest_seconds ?? 90));
    setEditingRest(true);
    setTimeout(() => restInputRef.current?.focus(), 0);
  }

  const commitRestEdit = useCallback(() => {
    const parsed = parseInt(restInput, 10);
    if (!isNaN(parsed) && parsed >= 0 && parsed <= 600) {
      updatePrefs.mutate({ rest_seconds: parsed });
    }
    setEditingRest(false);
  }, [restInput, updatePrefs]);

  function handleRestKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') commitRestEdit();
    if (e.key === 'Escape') setEditingRest(false);
  }

  // ------------- Units toggle -------------
  function handleUnitsToggle(units: 'kg' | 'lb') {
    if (units !== prefs?.units) {
      updatePrefs.mutate({ units });
    }
  }

  // ------------- Change password state -------------
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
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
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

  // ------------- Logout -------------
  async function handleLogout() {
    const refreshToken = useAuthStore.getState().refreshToken;
    if (refreshToken) {
      try {
        await apiFetch<void>('/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch {
        // ignore — local logout happens regardless
      }
    }
    logout();
    navigate('/login');
  }

  return (
    <div className="max-w-sm space-y-6">
      {/* Page title */}
      <h1 className="font-bold text-2xl text-text">Mi Perfil</h1>

      {/* ─── Stats bar ─── */}
      <div className="rounded-card border border-border bg-card">
        {statsLoading ? (
          <div className="flex justify-center py-6">
            <Spinner />
          </div>
        ) : (
          <div className="flex divide-x divide-border">
            <StatTile value={stats?.total_sessions} label="Sesiones" />
            <StatTile value={stats?.streak} label="Racha" />
            <StatTile value={stats?.total_prs} label="PRs" />
          </div>
        )}
      </div>

      {/* ─── Preferences ─── */}
      <div className="rounded-card border border-border bg-surface p-5 space-y-5">
        <h2 className="font-bold text-base text-text">Preferencias</h2>

        {prefsLoading ? (
          <Spinner />
        ) : (
          <>
            {/* Rest timer */}
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-text">Descanso entre series</p>
                <p className="text-xs text-muted mt-0.5">Tiempo de descanso por defecto</p>
              </div>

              {editingRest ? (
                <input
                  ref={restInputRef}
                  type="number"
                  value={restInput}
                  min={0}
                  max={600}
                  onChange={(e) => setRestInput(e.target.value)}
                  onBlur={commitRestEdit}
                  onKeyDown={handleRestKeyDown}
                  aria-label="Segundos de descanso"
                  className="w-20 text-center text-sm font-semibold rounded-input border border-border text-text"
                  style={{ height: '36px' }}
                />
              ) : (
                <button
                  onClick={startEditRest}
                  className="text-sm font-semibold text-accent border border-accent rounded-btn px-3 hover:bg-accent hover:text-bg transition-colors"
                  style={{ height: '36px', cursor: 'pointer', backgroundColor: 'transparent' }}
                  aria-label="Editar tiempo de descanso"
                >
                  {prefs?.rest_seconds ?? 90}s
                </button>
              )}
            </div>

            {/* Units toggle */}
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-text">Unidades de peso</p>
                <p className="text-xs text-muted mt-0.5">Para series y estadísticas</p>
              </div>

              <div className="flex rounded-btn overflow-hidden border border-border" role="group" aria-label="Unidades de peso">
                {(['kg', 'lb'] as const).map((unit) => {
                  const active = prefs?.units === unit;
                  return (
                    <button
                      key={unit}
                      onClick={() => handleUnitsToggle(unit)}
                      className={[
                        'text-xs font-bold px-4 transition-colors',
                        active
                          ? 'bg-accent text-bg'
                          : 'bg-transparent text-muted hover:text-text',
                      ].join(' ')}
                      style={{ height: '36px', cursor: 'pointer', border: 'none' }}
                      aria-pressed={active}
                    >
                      {unit}
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>

      {/* ─── Account info ─── */}
      <div className="rounded-card border border-border bg-surface p-5 space-y-4">
        <h2 className="font-bold text-base text-text">Cuenta</h2>

        {/* Avatar + email */}
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-elevated flex items-center justify-center shrink-0">
            <User size={24} className="text-muted" />
          </div>
          <div className="min-w-0">
            {displayName && (
              <p className="font-semibold text-sm text-text truncate capitalize">
                {displayName}
              </p>
            )}
            <p className="text-xs text-muted truncate">{user?.email}</p>
          </div>
        </div>

        <hr className="border-border" />

        {/* Change password */}
        <div>
          <h3 className="font-semibold text-sm text-text mb-3">Cambiar contraseña</h3>
          <form onSubmit={handleChangePassword} className="space-y-3">
            <div>
              <label htmlFor="current-password" className="block text-xs font-semibold mb-1 text-muted">
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
                  height: '40px',
                  borderRadius: '10px',
                  border: '1px solid var(--border)',
                  padding: '0 12px',
                  fontSize: '14px',
                }}
              />
            </div>
            <div>
              <label htmlFor="new-password" className="block text-xs font-semibold mb-1 text-muted">
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
                  height: '40px',
                  borderRadius: '10px',
                  border: '1px solid var(--border)',
                  padding: '0 12px',
                  fontSize: '14px',
                }}
              />
            </div>
            <div>
              <label htmlFor="confirm-new-password" className="block text-xs font-semibold mb-1 text-muted">
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
                  height: '40px',
                  borderRadius: '10px',
                  border: '1px solid var(--border)',
                  padding: '0 12px',
                  fontSize: '14px',
                }}
              />
            </div>

            {pwSuccess && <p className="text-xs text-accent">{pwSuccess}</p>}
            {pwError && <p className="text-xs text-danger">{pwError}</p>}

            <button
              type="submit"
              disabled={pwLoading}
              className="w-full font-semibold transition-all duration-200 disabled:opacity-60 rounded-btn bg-accent text-bg"
              style={{ height: '44px', fontSize: '14px', border: 'none', cursor: 'pointer' }}
            >
              {pwLoading ? 'Guardando…' : 'Actualizar contraseña'}
            </button>
          </form>
        </div>
      </div>

      {/* ─── Logout ─── */}
      <button
        onClick={handleLogout}
        className="w-full flex items-center justify-center gap-2 font-semibold rounded-btn border border-border text-muted transition-colors hover:text-danger hover:border-danger"
        style={{ height: '48px', backgroundColor: 'transparent', cursor: 'pointer' }}
      >
        <LogOut size={18} />
        Cerrar sesión
      </button>
    </div>
  );
}
