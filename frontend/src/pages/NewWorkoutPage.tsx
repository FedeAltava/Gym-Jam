import { useNavigate, Link } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft } from 'lucide-react';
import { useCreateWorkout } from '../hooks/useWorkouts';
import { DAYS, DAY_LABEL } from '../lib/days';

const schema = z.object({
  name: z.string().min(1, 'El nombre es requerido').max(100),
  description: z.string().max(500).optional(),
  training_days: z
    .array(z.string())
    .min(1, 'Selecciona al menos un día de entrenamiento'),
});
type Form = z.infer<typeof schema>;

export function NewWorkoutPage() {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { training_days: [] },
  });
  const createMutation = useCreateWorkout();

  return (
    <div>
      {/* Back */}
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-1.5 text-sm font-semibold mb-5 text-muted no-underline"
      >
        <ArrowLeft size={16} /> Volver
      </Link>

      <h1 className="font-bold mb-1 text-2xl text-text">Nuevo Entrenamiento</h1>
      <p className="text-sm mb-6 text-muted">Define tu plan de entrenamiento</p>

      <div className="max-w-lg rounded-card border border-border bg-surface p-5">
        <form
          onSubmit={handleSubmit((d) =>
            createMutation.mutate(
              {
                name: d.name,
                description: d.description,
                training_days: d.training_days,
              },
              { onSuccess: (w) => navigate(`/workouts/${w.id}`) },
            ),
          )}
          className="space-y-5"
        >
          <div>
            <label
              htmlFor="nw-name"
              className="block font-semibold mb-2 text-text text-sm"
            >
              Nombre *
            </label>
            <input
              id="nw-name"
              {...register('name')}
              placeholder="Ej. Push Day"
              className="w-full"
              style={{
                height: '44px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                padding: '0 12px',
                fontSize: '16px',
              }}
            />
            {errors.name && (
              <p className="mt-1 text-xs text-danger">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label
              htmlFor="nw-description"
              className="block font-semibold mb-2 text-text text-sm"
            >
              Descripción
            </label>
            <textarea
              id="nw-description"
              {...register('description')}
              placeholder="Descripción opcional…"
              rows={3}
              className="w-full resize-none"
              style={{
                borderRadius: '10px',
                border: '1px solid var(--border)',
                padding: '10px 12px',
                fontSize: '16px',
              }}
            />
          </div>

          <div>
            <label className="block font-semibold mb-2 text-text text-sm">
              Días de entrenamiento
            </label>
            <Controller
              name="training_days"
              control={control}
              render={({ field }) => (
                <div className="grid grid-cols-2 gap-2">
                  {DAYS.map((day) => {
                    const checked = field.value.includes(day);
                    return (
                      <label
                        key={day}
                        className="flex items-center gap-2.5 px-3 py-2.5 rounded-btn cursor-pointer transition-all text-sm font-semibold select-none"
                        style={{
                          border: `1px solid ${checked ? 'var(--neon-green)' : 'var(--border)'}`,
                          backgroundColor: checked
                            ? 'rgba(0, 255, 135, 0.1)'
                            : 'var(--bg-elevated)',
                          color: checked ? 'var(--neon-green)' : 'var(--text-muted)',
                        }}
                      >
                        <input
                          type="checkbox"
                          className="sr-only"
                          checked={checked}
                          onChange={(e) => {
                            if (e.target.checked)
                              field.onChange([...field.value, day]);
                            else
                              field.onChange(
                                field.value.filter((d: string) => d !== day),
                              );
                          }}
                        />
                        <span
                          className="w-4 h-4 rounded flex items-center justify-center shrink-0"
                          style={{
                            border: `1px solid ${checked ? 'var(--neon-green)' : 'var(--text-muted)'}`,
                            backgroundColor: checked ? 'var(--neon-green)' : 'transparent',
                          }}
                        >
                          {checked && (
                            <span
                              style={{
                                color: 'var(--bg)',
                                fontSize: '10px',
                                lineHeight: 1,
                                fontWeight: 700,
                              }}
                            >
                              ✓
                            </span>
                          )}
                        </span>
                        {DAY_LABEL[day]}
                      </label>
                    );
                  })}
                </div>
              )}
            />
            {errors.training_days && (
              <p className="mt-2 text-xs text-danger">
                {errors.training_days.message}
              </p>
            )}
          </div>

          {createMutation.isError && (
            <p className="text-xs text-danger">
              {(createMutation.error as Error).message}
            </p>
          )}

          <div className="flex gap-3 pt-1">
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex-1 font-semibold transition-all duration-200 disabled:opacity-60 rounded-btn bg-accent text-bg"
              style={{
                height: '48px',
                fontSize: '15px',
                border: 'none',
                cursor: 'pointer',
                boxShadow: '0 0 16px rgba(0, 255, 135, 0.4)',
              }}
            >
              {createMutation.isPending ? 'Creando…' : 'Crear Entrenamiento'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="font-semibold rounded-btn border border-border text-muted"
              style={{
                height: '48px',
                padding: '0 24px',
                backgroundColor: 'transparent',
                fontSize: '15px',
                cursor: 'pointer',
              }}
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
