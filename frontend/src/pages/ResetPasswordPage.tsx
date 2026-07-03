import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { apiFetch } from '../lib/api';

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [validationError, setValidationError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setValidationError('');

    if (newPassword !== confirmPassword) {
      setValidationError('Las contraseñas no coinciden.');
      return;
    }

    setLoading(true);
    try {
      await apiFetch<void>('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({ token, new_password: newPassword }),
      });
      setSuccess(true);
    } catch {
      setError('El enlace es inválido o ya expiró.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-bg">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="font-bold tracking-tight" style={{ fontSize: '32px' }}>
            <span className="text-text">Gym</span>
            <span className="text-accent">Jam</span>
          </h1>
        </div>

        <div className="rounded-card border border-border bg-surface p-6">
          <h2 className="font-bold mb-5 text-lg text-text">Nueva contraseña</h2>

          {success ? (
            <div className="space-y-4">
              <p className="text-sm text-text">
                Contraseña actualizada. Podés iniciar sesión.
              </p>
              <Link
                to="/login"
                className="block text-center font-semibold text-info no-underline text-sm"
              >
                Ir al inicio de sesión
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="reset-new-password"
                  className="block font-semibold mb-2 text-text text-sm"
                >
                  Nueva contraseña
                </label>
                <input
                  id="reset-new-password"
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
                  htmlFor="reset-confirm-password"
                  className="block font-semibold mb-2 text-text text-sm"
                >
                  Confirmar contraseña
                </label>
                <input
                  id="reset-confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
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

              {validationError && (
                <p className="text-xs text-danger">{validationError}</p>
              )}
              {error && <p className="text-xs text-danger">{error}</p>}

              <button
                type="submit"
                disabled={loading}
                className="w-full font-semibold transition-all duration-200 disabled:opacity-60 rounded-btn bg-accent text-bg"
                style={{
                  height: '48px',
                  fontSize: '16px',
                  border: 'none',
                  cursor: 'pointer',
                  marginTop: '8px',
                  boxShadow: '0 0 16px rgba(0, 255, 135, 0.4)',
                }}
              >
                {loading ? 'Guardando…' : 'Cambiar contraseña'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
