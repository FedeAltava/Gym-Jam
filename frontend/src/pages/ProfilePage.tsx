import { useState, useCallback, useRef } from 'react';
import { LogOut, Calendar, Clock, ChevronDown } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { useUserStats } from '../hooks/useStats';
import { useUserPreferences, useUpdatePreferences } from '../hooks/useUserPreferences';
import { useActiveWorkout } from '../hooks/useActiveWorkout';
import { useChangePassword } from '../hooks/useProfile';
import { useLogout } from '../hooks/useAuth';
import { Spinner } from '../components/Spinner';
import { DAY_SHORT } from '../lib/days';
import type { DayKey } from '../lib/days';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Format rest_seconds as "M:SS" (e.g. 90 → "1:30") */
function formatRestTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

/** Format ISO date as "Month YYYY" in Spanish (e.g. "julio 2026") */
function formatMemberSince(isoDate: string): string {
  return new Intl.DateTimeFormat('es-ES', { month: 'long', year: 'numeric' }).format(
    new Date(isoDate),
  );
}

// ---------------------------------------------------------------------------
// StatTile
// ---------------------------------------------------------------------------

interface StatTileProps {
  value: number | undefined;
  label: string;
}

function StatTile({ value, label }: StatTileProps) {
  return (
    <div
      style={{
        flex: 1,
        padding: '16px',
        borderRadius: '18px',
        background: 'var(--card-bg)',
        border: '1px solid rgba(255,255,255,0.07)',
        textAlign: 'center',
      }}
    >
      <div
        style={{
          fontSize: '24px',
          fontWeight: 800,
          color: 'var(--neon-green)',
          fontFamily: "'Barlow Semi Condensed', sans-serif",
          lineHeight: 1,
        }}
      >
        {value ?? '—'}
      </div>
      <div
        style={{
          fontSize: '11px',
          color: 'var(--text-muted)',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          marginTop: '4px',
        }}
      >
        {label}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ProfilePage
// ---------------------------------------------------------------------------

export function ProfilePage() {
  const { user } = useAuthStore();

  const { data: stats, isLoading: statsLoading } = useUserStats();
  const { data: prefs, isLoading: prefsLoading } = useUserPreferences();
  const updatePrefs = useUpdatePreferences();
  const { activeWorkout } = useActiveWorkout();
  const changePasswordMutation = useChangePassword();
  const logoutMutation = useLogout();

  // Derive display name from email (before the @), capitalize words
  const displayName = user?.email
    ? user.email
        .split('@')[0]
        .replace(/[._-]/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase())
    : '';

  const avatarLetter = displayName ? displayName[0].toUpperCase() : '?';

  // Training days from active workout
  const trainingDaysLabel = activeWorkout?.training_days
    ? activeWorkout.training_days
        .map((d) => DAY_SHORT[d.day_of_week as DayKey] ?? d.day_of_week)
        .join(', ')
    : null;

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

  // ------------- Change password state -------------
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [pwSuccess, setPwSuccess] = useState('');
  const [pwError, setPwError] = useState('');

  function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    setPwSuccess('');
    setPwError('');

    if (newPassword !== confirmNewPassword) {
      setPwError('Las nuevas contraseñas no coinciden.');
      return;
    }

    changePasswordMutation.mutate(
      { current_password: currentPassword, new_password: newPassword },
      {
        onSuccess: () => {
          setPwSuccess('Contraseña actualizada.');
          setCurrentPassword('');
          setNewPassword('');
          setConfirmNewPassword('');
        },
        onError: () => {
          setPwError('La contraseña actual es incorrecta.');
        },
      },
    );
  }

  return (
    <div style={{ maxWidth: '420px' }}>
      <div style={{ fontSize: '27px', fontWeight: 700, color: '#EAF0EA', fontFamily: "'Barlow Semi Condensed', sans-serif", marginBottom: '18px' }}>
        Mi Perfil
      </div>

      {/* ─── Profile card ─── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          padding: '20px',
          borderRadius: '22px',
          background: 'linear-gradient(135deg, rgb(18,48,33), rgb(12,26,18))',
          border: '1px solid rgba(43,229,129,0.2)',
          marginBottom: '16px',
        }}
      >
        {/* Avatar */}
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '20px',
            background: 'linear-gradient(135deg, rgb(43,229,129), rgb(31,189,106))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '26px',
            fontWeight: 800,
            color: 'rgb(6,33,15)',
            fontFamily: "'Barlow Semi Condensed', sans-serif",
            flexShrink: 0,
          }}
        >
          {avatarLetter}
        </div>
        <div>
          <div
            style={{
              fontSize: '19px',
              fontWeight: 700,
              color: 'var(--text)',
              fontFamily: "'Barlow Semi Condensed', sans-serif",
            }}
          >
            {displayName || user?.email}
          </div>
          {user?.created_at && (
            <div
              style={{
                fontSize: '13px',
                color: 'rgb(159,176,162)',
                fontWeight: 500,
                marginTop: '2px',
              }}
            >
              Miembro desde {formatMemberSince(user.created_at)}
            </div>
          )}
        </div>
      </div>

      {/* ─── Stats bar ─── */}
      <div
        style={{
          display: 'flex',
          gap: '10px',
          marginBottom: '16px',
        }}
      >
        {statsLoading ? (
          <div style={{ flex: 1, display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
            <Spinner />
          </div>
        ) : (
          <>
            <StatTile value={stats?.total_sessions} label="Sesiones" />
            <StatTile value={stats?.streak} label="Racha" />
            <StatTile value={stats?.total_prs} label="PRs" />
          </>
        )}
      </div>

      {/* ─── Settings list ─── */}
      <div
        style={{
          borderRadius: '20px',
          background: 'rgb(15,19,15)',
          border: '1px solid rgba(255,255,255,0.06)',
          overflow: 'hidden',
          marginBottom: '16px',
        }}
      >
        {prefsLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
            <Spinner />
          </div>
        ) : (
          <>
            {/* Training days row */}
            {trainingDaysLabel !== null && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px',
                  padding: '16px',
                  borderBottom: '1px solid rgba(255,255,255,0.05)',
                }}
              >
                <Calendar size={18} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                <span
                  style={{
                    flex: 1,
                    fontSize: '15px',
                    fontWeight: 600,
                    color: 'var(--text)',
                  }}
                >
                  Días de entrenamiento
                </span>
                <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  {trainingDaysLabel}
                </span>
              </div>
            )}

            {/* Rest timer row */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                padding: '16px',
              }}
            >
              <Clock size={18} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
              <span
                style={{
                  flex: 1,
                  fontSize: '15px',
                  fontWeight: 600,
                  color: 'var(--text)',
                }}
              >
                Descanso entre series
              </span>

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
                  style={{
                    width: '64px',
                    textAlign: 'center',
                    fontSize: '13px',
                    fontWeight: 600,
                    height: '32px',
                    borderRadius: '8px',
                    border: '1px solid var(--border)',
                    color: 'var(--text)',
                  }}
                />
              ) : (
                <button
                  onClick={startEditRest}
                  aria-label="Editar tiempo de descanso"
                  style={{
                    fontSize: '13px',
                    color: 'var(--text-muted)',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    padding: 0,
                  }}
                >
                  {prefs?.rest_seconds != null
                    ? `${formatRestTime(prefs.rest_seconds)} (${prefs.rest_seconds}s)`
                    : '90s'}
                </button>
              )}
            </div>
          </>
        )}
      </div>

      {/* ─── Change password ─── */}
      <div
        style={{
          borderRadius: '20px',
          background: 'rgb(15,19,15)',
          border: '1px solid rgba(255,255,255,0.06)',
          overflow: 'hidden',
          marginBottom: '16px',
        }}
      >
        <button
          onClick={() => setShowPasswordForm((v) => !v)}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            padding: '16px',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            textAlign: 'left',
          }}
        >
          <span style={{ flex: 1, fontSize: '15px', fontWeight: 600, color: 'var(--text)' }}>
            Cambiar contraseña
          </span>
          <ChevronDown
            size={18}
            style={{
              color: 'var(--text-muted)',
              transition: 'transform 0.2s',
              transform: showPasswordForm ? 'rotate(180deg)' : 'rotate(0deg)',
            }}
          />
        </button>

        {showPasswordForm && (
          <form
            onSubmit={handleChangePassword}
            style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '0 16px 16px' }}
          >
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
                style={{ height: '40px', borderRadius: '10px', border: '1px solid var(--border)', padding: '0 12px', fontSize: '14px' }}
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
                style={{ height: '40px', borderRadius: '10px', border: '1px solid var(--border)', padding: '0 12px', fontSize: '14px' }}
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
                style={{ height: '40px', borderRadius: '10px', border: '1px solid var(--border)', padding: '0 12px', fontSize: '14px' }}
              />
            </div>

            {pwSuccess && <p className="text-xs text-accent">{pwSuccess}</p>}
            {pwError && <p className="text-xs text-danger">{pwError}</p>}

            <button
              type="submit"
              disabled={changePasswordMutation.isPending}
              className="w-full font-semibold transition-all duration-200 disabled:opacity-60 rounded-btn bg-accent text-bg"
              style={{ height: '44px', fontSize: '14px', border: 'none', cursor: 'pointer' }}
            >
              {changePasswordMutation.isPending ? 'Guardando…' : 'Actualizar contraseña'}
            </button>
          </form>
        )}
      </div>

      {/* ─── Logout ─── */}
      <button
        onClick={() => logoutMutation.mutate()}
        disabled={logoutMutation.isPending}
        style={{
          width: '100%',
          height: '52px',
          border: '1px solid rgba(255,91,91,0.3)',
          borderRadius: '16px',
          background: 'rgba(255,91,91,0.08)',
          color: 'rgb(255,123,123)',
          fontSize: '15px',
          fontWeight: 700,
          fontFamily: 'Barlow, sans-serif',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          cursor: 'pointer',
        }}
      >
        <LogOut size={18} />
        Cerrar sesión
      </button>
    </div>
  );
}
