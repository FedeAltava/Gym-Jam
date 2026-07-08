import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { useRegisterMutation } from '../hooks/useAuth';

const schema = z
  .object({
    email: z.string().email('Email inválido'),
    password: z.string().min(8, 'Mínimo 8 caracteres'),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: 'Las contraseñas no coinciden',
    path: ['confirmPassword'],
  });
type Form = z.infer<typeof schema>;

export function RegisterPage() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Form>({ resolver: zodResolver(schema) });
  const registerMutation = useRegisterMutation();
  const [show, setShow] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-bg">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="font-bold tracking-tight" style={{ fontSize: '32px' }}>
            <span className="text-text">Gym</span>
            <span className="text-accent">Jam</span>
          </h1>
          <p className="mt-2 text-sm text-muted">Comienza tu journey fitness hoy.</p>
        </div>

        {/* Card */}
        <div className="rounded-card border border-border bg-surface p-6">
          <h2 className="font-bold mb-5 text-lg text-text">Crear cuenta</h2>

          <form
            onSubmit={handleSubmit(({ email, password }) =>
              registerMutation.mutate({ email, password }),
            )}
            className="space-y-4"
          >
            <div>
              <label
                htmlFor="reg-email"
                className="block font-semibold mb-2 text-text text-sm"
              >
                Email
              </label>
              <input
                id="reg-email"
                type="email"
                {...register('email')}
                placeholder="tu@email.com"
                className="w-full"
                style={{
                  height: '44px',
                  borderRadius: '10px',
                  border: '1px solid var(--border)',
                  padding: '0 12px',
                  fontSize: '16px',
                }}
              />
              {errors.email && (
                <p className="mt-1 text-xs text-danger">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label
                htmlFor="reg-password"
                className="block font-semibold mb-2 text-text text-sm"
              >
                Contraseña
              </label>
              <div className="relative">
                <input
                  id="reg-password"
                  type={show ? 'text' : 'password'}
                  {...register('password')}
                  placeholder="••••••••"
                  className="w-full"
                  style={{
                    height: '44px',
                    borderRadius: '10px',
                    border: '1px solid var(--border)',
                    padding: '0 40px 0 12px',
                    fontSize: '16px',
                  }}
                />
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShow((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted"
                  style={{ minHeight: 'unset', background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  {show ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-danger">{errors.password.message}</p>
              )}
            </div>

            <div>
              <label
                htmlFor="reg-confirm"
                className="block font-semibold mb-2 text-text text-sm"
              >
                Confirmar contraseña
              </label>
              <div className="relative">
                <input
                  id="reg-confirm"
                  type={showConfirm ? 'text' : 'password'}
                  {...register('confirmPassword')}
                  placeholder="••••••••"
                  className="w-full"
                  style={{
                    height: '44px',
                    borderRadius: '10px',
                    border: '1px solid var(--border)',
                    padding: '0 40px 0 12px',
                    fontSize: '16px',
                  }}
                />
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShowConfirm((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted"
                  style={{ minHeight: 'unset', background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-xs text-danger">
                  {errors.confirmPassword.message}
                </p>
              )}
            </div>

            {registerMutation.isError && (
              <p className="text-xs text-danger">
                {(registerMutation.error as Error).message}
              </p>
            )}
            {registerMutation.isSuccess && (
              <p className="text-xs text-accent">¡Cuenta creada! Redirigiendo…</p>
            )}

            <button
              type="submit"
              disabled={registerMutation.isPending}
              className="w-full font-semibold transition-all duration-200 disabled:opacity-60 rounded-btn bg-accent text-bg"
              style={{
                height: '48px',
                fontSize: '16px',
                border: 'none',
                cursor: 'pointer',
                marginTop: '8px',
                boxShadow: '0 0 16px var(--neon-glow)',
              }}
            >
              {registerMutation.isPending ? 'Creando…' : 'Crear cuenta'}
            </button>

            <p className="text-center text-sm pt-1 text-muted">
              ¿Ya tienes cuenta?{' '}
              <Link to="/login" className="font-semibold text-info no-underline">
                Iniciar sesión
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
