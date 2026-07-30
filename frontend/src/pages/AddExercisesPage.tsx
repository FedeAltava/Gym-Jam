import { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useExercises } from '../hooks/useExercises';
import { apiFetch } from '../lib/api';
import { Spinner } from '../components/Spinner';
import type { WorkoutResponse } from '../types/api';

const DAY_LABEL: Record<string, string> = {
  MONDAY: 'Lunes',
  TUESDAY: 'Martes',
  WEDNESDAY: 'Miércoles',
  THURSDAY: 'Jueves',
  FRIDAY: 'Viernes',
  SATURDAY: 'Sábado',
  SUNDAY: 'Domingo',
};

export function AddExercisesPage() {
  const { workoutId, day } = useParams<{ workoutId: string; day: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [selectedMuscleGroup, setSelectedMuscleGroup] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [isPending, setIsPending] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const { data: exercises, isLoading, isError } = useExercises();
  const { data: workout } = useQuery({
    queryKey: ['workouts', workoutId],
    queryFn: () => apiFetch<WorkoutResponse>(`/workouts/${workoutId}`),
    enabled: Boolean(workoutId),
  });

  const trainingDay = workout?.training_days.find((d) => d.day_of_week === day);
  const usedIds = new Set(trainingDay?.exercises.map((e) => e.exercise_id) ?? []);

  const catalog = exercises ?? [];
  const muscleGroups = [...new Set(catalog.map((e) => e.muscle_group))].sort();
  const displayed = catalog
    .filter(
      (e) =>
        !usedIds.has(e.id) &&
        (selectedMuscleGroup === null || e.muscle_group === selectedMuscleGroup),
    )
    .sort((a, b) => {
      const mg = a.muscle_group.localeCompare(b.muscle_group);
      return mg !== 0 ? mg : a.name.localeCompare(b.name);
    });

  function toggle(id: string) {
    setSelected((prev) => {
      if (prev.has(id)) {
        return new Set([...prev].filter((x) => x !== id));
      }
      return new Set([...prev, id]);
    });
  }

  async function handleAdd() {
    if (!workoutId || !day || selected.size === 0 || isPending) return;
    setIsPending(true);
    setAddError(null);

    let succeeded = 0;
    let failed = 0;
    for (const id of selected) {
      try {
        await apiFetch(`/workouts/${workoutId}/training-days/${day}/exercises`, {
          method: 'POST',
          body: JSON.stringify({ exercise_id: id }),
        });
        succeeded++;
      } catch {
        failed++;
        break;
      }
    }

    await queryClient.invalidateQueries({ queryKey: ['workouts', workoutId] });

    setIsPending(false);

    if (failed === 0) {
      navigate(`/workouts/${workoutId}`);
    } else if (succeeded > 0) {
      // Partial success: some exercises were added; navigate back and show error.
      setAddError(
        `Se añadieron ${succeeded} ejercicio${succeeded !== 1 ? 's' : ''}, pero ${failed} no se pudo${failed !== 1 ? 'n' : ''} añadir. Inténtalo de nuevo.`,
      );
      navigate(`/workouts/${workoutId}`);
    } else {
      // All failed: stay on page so the user can retry.
      setAddError('No se pudieron añadir los ejercicios. Inténtalo de nuevo.');
    }
  }

  const dayLabel = day ? DAY_LABEL[day] ?? day : '';

  return (
    <div style={{ backgroundColor: 'var(--bg)', minHeight: '100vh' }}>
      <header className="bg-surface border-b border-border sticky top-0 z-10 px-4 py-3 flex items-center gap-3">
        <Link
          to={`/workouts/${workoutId}`}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-muted no-underline shrink-0"
        >
          <ArrowLeft size={16} /> Volver
        </Link>
        <h1 className="font-bold text-base text-text flex-1 min-w-0 truncate">
          Añadir ejercicios al {dayLabel}
        </h1>
      </header>

      {muscleGroups.length > 0 && (
        <div
          className="flex gap-2 overflow-x-auto px-4 py-2 sticky top-[57px] z-10 border-b border-border"
          style={{ backgroundColor: 'var(--bg)' }}
          role="group"
          aria-label="Filtrar por grupo muscular"
        >
          <button
            onClick={() => setSelectedMuscleGroup(null)}
            className="text-xs font-semibold rounded-btn shrink-0"
            style={{
              height: '28px',
              padding: '0 12px',
              cursor: 'pointer',
              backgroundColor: selectedMuscleGroup === null ? 'var(--neon-green)' : 'var(--bg-elevated)',
              color: selectedMuscleGroup === null ? 'var(--bg)' : 'var(--text-muted)',
              border: selectedMuscleGroup === null ? '1px solid var(--neon-green)' : '1px solid var(--border)',
            }}
          >
            Todos
          </button>
          {muscleGroups.map((mg) => (
            <button
              key={mg}
              onClick={() => setSelectedMuscleGroup(mg)}
              className="text-xs font-semibold rounded-btn shrink-0"
              style={{
                height: '28px',
                padding: '0 12px',
                cursor: 'pointer',
                backgroundColor: selectedMuscleGroup === mg ? 'var(--neon-green)' : 'var(--bg-elevated)',
                color: selectedMuscleGroup === mg ? 'var(--bg)' : 'var(--text-muted)',
                border: selectedMuscleGroup === mg ? '1px solid var(--neon-green)' : '1px solid var(--border)',
              }}
            >
              {mg}
            </button>
          ))}
        </div>
      )}

      <div className="pb-[140px] md:pb-24">
        {isLoading ? (
          <Spinner />
        ) : isError ? (
          <p className="text-sm text-danger px-4 py-6">
            No se pudo cargar el catálogo de ejercicios. Inténtalo de nuevo.
          </p>
        ) : displayed.length === 0 ? (
          <p className="text-sm italic text-muted px-4 py-6">
            No hay ejercicios disponibles.
          </p>
        ) : (
          <ul>
            {displayed.map((exercise) => {
              const isSelected = selected.has(exercise.id);
              return (
                <li
                  key={exercise.id}
                  onClick={() => toggle(exercise.id)}
                  className="flex items-center gap-3 px-4 py-3 border-b border-border cursor-pointer"
                  role="checkbox"
                  aria-checked={isSelected}
                >
                  <div
                    className="shrink-0 flex items-center justify-center"
                    style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      border: isSelected ? '1px solid var(--neon-green)' : '1px solid var(--border)',
                      backgroundColor: isSelected ? 'var(--neon-green)' : 'transparent',
                      color: '#fff',
                      fontSize: '13px',
                      fontWeight: 700,
                    }}
                  >
                    {isSelected ? '✓' : ''}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-text truncate">
                      {exercise.name}
                    </p>
                    <p className="text-xs text-muted">{exercise.muscle_group}</p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div
        className="fixed bottom-[60px] md:bottom-0 left-0 right-0 p-4 border-t border-border"
        style={{ backgroundColor: 'var(--bg)' }}
      >
        {addError && (
          <p className="mb-2 text-xs text-danger">{addError}</p>
        )}
        <button
          onClick={() => void handleAdd()}
          disabled={selected.size === 0 || isPending}
          className={`w-full text-sm rounded-btn ${
            selected.size === 0 || isPending ? 'opacity-50 cursor-not-allowed' : ''
          }`}
          style={{
            height: '48px',
            border: 'none',
            cursor: selected.size === 0 || isPending ? 'not-allowed' : 'pointer',
            backgroundColor: 'var(--neon-green)',
            color: 'var(--bg)',
            fontWeight: 600,
          }}
        >
          {isPending
            ? 'Añadiendo…'
            : `Añadir ${selected.size} ejercicio${selected.size !== 1 ? 's' : ''}`}
        </button>
      </div>
    </div>
  );
}
