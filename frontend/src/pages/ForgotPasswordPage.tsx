import { useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../lib/api';

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await apiFetch<void>('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email }),
      });
      setSubmitted(true);
    } catch {
      setError('Ocurrió un error. Intenta nuevamente.');
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
          <h2 className="font-bold mb-5 text-lg text-text">Recuperar contraseña</h2>

          {submitted ? (
            <p className="text-sm text-text">
              Si tu email está registrado, recibirás un enlace en breve.
            </p>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="forgot-email"
                  className="block font-semibold mb-2 text-text text-sm"
                >
                  Email
                </label>
                <input
                  id="forgot-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="tu@email.com"
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
                {loading ? 'Enviando…' : 'Enviar enlace'}
              </button>
            </form>
          )}

          <p className="text-center text-sm pt-4 text-muted">
            <Link to="/login" className="font-semibold text-info no-underline">
              Volver al inicio de sesión
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
