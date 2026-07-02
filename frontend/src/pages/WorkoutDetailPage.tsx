import { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Trash2 } from 'lucide-react';
import { useWorkout, useDeleteWorkout } from '../hooks/useWorkouts';
import { Spinner } from '../components/Spinner';
import { DAY_LABEL } from '../lib/days';

export function WorkoutDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: workout, isLoading, isError, error } = useWorkout(id ?? '');
  const deleteMutation = useDeleteWorkout();
  const [confirmDelete, setConfirmDelete] = useState(false);

  if (isLoading) return <Spinner />;
  if (isError)
    return (
      <p className="text-sm text-danger">Error: {(error as Error).message}</p>
    );
  if (!workout) return null;

  function handleDelete() {
    if (!id) return;
    deleteMutation.mutate(id, {
      onSuccess: () => navigate('/dashboard'),
    });
  }

  return (
    <div>
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-1.5 text-sm font-semibold mb-5 text-muted no-underline"
      >
        <ArrowLeft size={16} /> Volver
      </Link>

      <div className="flex items-start gap-3 mb-6">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="font-bold text-2xl text-text">{workout.name}</h1>
            {workout.is_active && (
              <span
                className="text-xs font-semibold px-2 py-0.5 rounded-full text-accent"
                style={{
                  backgroundColor: 'rgba(0, 255, 135, 0.1)',
                  border: '1px solid rgba(0, 255, 135, 0.3)',
                }}
              >
                Activo
              </span>
            )}
          </div>
          {workout.description && (
            <p className="text-sm mt-1 text-muted">{workout.description}</p>
          )}
        </div>

        {/* Delete button with inline confirm */}
        <div className="flex items-center gap-2 shrink-0">
          {!confirmDelete ? (
            <button
              onClick={() => setConfirmDelete(true)}
              className="flex items-center gap-1.5 text-sm font-semibold rounded-btn border border-danger text-danger transition-colors hover:bg-danger hover:text-bg"
              style={{ height: '36px', padding: '0 12px', backgroundColor: 'transparent', cursor: 'pointer' }}
              aria-label="Eliminar entrenamiento"
            >
              <Trash2 size={15} />
              Eliminar
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted font-semibold">¿Seguro?</span>
              <button
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
                className="text-sm font-semibold rounded-btn bg-danger text-bg disabled:opacity-60"
                style={{ height: '36px', padding: '0 12px', border: 'none', cursor: 'pointer' }}
              >
                {deleteMutation.isPending ? '…' : 'Sí'}
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="text-sm font-semibold rounded-btn border border-border text-muted"
                style={{ height: '36px', padding: '0 12px', backgroundColor: 'transparent', cursor: 'pointer' }}
              >
                No
              </button>
            </div>
          )}
        </div>
      </div>

      {deleteMutation.isError && (
        <p className="mb-4 text-xs text-danger">
          {(deleteMutation.error as Error).message}
        </p>
      )}

      {workout.training_days.length === 0 ? (
        <div className="text-center py-16 rounded-card border-2 border-dashed border-border">
          <p className="text-sm italic text-muted">
            Sin días de entrenamiento configurados.
          </p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {workout.training_days.map((day) => (
            <div
              key={day.day_of_week}
              className="rounded-card border border-border bg-surface p-4"
            >
              <h3 className="font-bold mb-3 text-base text-text">
                {DAY_LABEL[day.day_of_week as keyof typeof DAY_LABEL] ??
                  day.day_of_week}
              </h3>
              {day.exercises.length === 0 ? (
                <p className="text-sm italic text-muted">Sin ejercicios</p>
              ) : (
                <ol className="space-y-2">
                  {day.exercises.map((ex) => (
                    <li key={ex.id} className="flex items-center gap-2 text-sm">
                      <span className="font-bold w-5 text-right shrink-0 text-accent">
                        {ex.order}.
                      </span>
                      <span className="font-mono text-xs px-2 py-1 rounded bg-elevated border border-border text-muted">
                        {ex.exercise_id.slice(0, 8)}…
                      </span>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
