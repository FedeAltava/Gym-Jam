import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useCreateWorkout } from '../../hooks/useWorkouts';
import { DAYS, DAY_LABEL, DAY_SHORT } from '../../lib/days';

const schema = z.object({
  name: z.string().trim().min(1, 'El nombre es obligatorio').max(100),
  description: z.string().trim().max(500).optional(),
  training_days: z.array(z.string()).min(1, 'Selecciona al menos un día'),
});
type FormValues = z.infer<typeof schema>;

interface NewRoutineModalProps {
  onClose: () => void;
}

export function NewRoutineModal({ onClose }: NewRoutineModalProps) {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', description: '', training_days: [] },
  });
  const createMutation = useCreateWorkout();

  const onSubmit = handleSubmit((data) =>
    createMutation.mutate(
      {
        name: data.name,
        description: data.description || undefined,
        training_days: data.training_days,
      },
      {
        onSuccess: (workout) => {
          onClose();
          navigate(`/workouts/${workout.id}`);
        },
      },
    ),
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Nueva rutina"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-card border border-border bg-card p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-condensed font-bold text-xl text-text">
            Nueva rutina
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="inline-flex items-center justify-center rounded text-muted bg-transparent border-none transition-colors hover:text-text"
            style={{ height: '28px', width: '28px', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div>
            <label
              htmlFor="nrm-name"
              className="block font-semibold mb-2 text-text text-sm"
            >
              Nombre *
            </label>
            <input
              id="nrm-name"
              {...register('name')}
              placeholder="Ej. Push Day"
              className="w-full rounded-input border border-border"
              style={{ height: '44px', padding: '0 12px' }}
            />
            {errors.name && (
              <p className="mt-1 text-xs text-danger">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label
              htmlFor="nrm-description"
              className="block font-semibold mb-2 text-text text-sm"
            >
              Descripción
            </label>
            <input
              id="nrm-description"
              {...register('description')}
              placeholder="Descripción opcional…"
              className="w-full rounded-input border border-border"
              style={{ height: '44px', padding: '0 12px' }}
            />
          </div>

          <div>
            <p className="font-semibold mb-2 text-text text-sm">
              Días de entrenamiento *
            </p>
            <Controller
              name="training_days"
              control={control}
              render={({ field }) => (
                <div className="flex flex-wrap gap-2">
                  {DAYS.map((day) => {
                    const selected = field.value.includes(day);
                    return (
                      <button
                        key={day}
                        type="button"
                        aria-pressed={selected}
                        aria-label={DAY_LABEL[day]}
                        onClick={() =>
                          field.onChange(
                            selected
                              ? field.value.filter((d) => d !== day)
                              : [...field.value, day],
                          )
                        }
                        className={[
                          'text-xs font-semibold rounded-full transition-colors',
                          selected
                            ? 'bg-[var(--accent-soft)] border border-border-accent text-accent'
                            : 'bg-transparent border border-border text-muted hover:text-text',
                        ].join(' ')}
                        style={{ height: '30px', padding: '0 12px', cursor: 'pointer' }}
                      >
                        {DAY_SHORT[day]}
                      </button>
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
              className="flex-1 font-semibold rounded-btn bg-accent text-bg neon-glow transition-opacity disabled:opacity-60"
              style={{ height: '44px', border: 'none', cursor: 'pointer' }}
            >
              {createMutation.isPending ? 'Creando…' : 'Crear rutina'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="font-semibold rounded-btn border border-border text-muted"
              style={{
                height: '44px',
                padding: '0 20px',
                backgroundColor: 'transparent',
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
