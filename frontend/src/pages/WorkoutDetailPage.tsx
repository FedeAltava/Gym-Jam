import { useState } from 'react';
import type { ChangeEvent } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, Trash2, X } from 'lucide-react';
import { useWorkout, useDeleteWorkout } from '../hooks/useWorkouts';
import {
  useExercises,
  useAddExercise,
  useRemoveExercise,
} from '../hooks/useExercises';
import { Spinner } from '../components/Spinner';
import { DAY_LABEL } from '../lib/days';
import type { ExerciseResponse, TrainingDayResponse } from '../types/api';

interface TrainingDayCardProps {
  workoutId: string;
  day: TrainingDayResponse;
  catalog: ExerciseResponse[];
  catalogLoading: boolean;
  catalogError: boolean;
}

function TrainingDayCard({
  workoutId,
  day,
  catalog,
  catalogLoading,
  catalogError,
}: TrainingDayCardProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const addMutation = useAddExercise(workoutId);
  const removeMutation = useRemoveExercise(workoutId);

  const exerciseById = new Map(catalog.map((e) => [e.id, e]));

  // The backend rejects duplicates per day, so hide already-added exercises.
  const usedIds = new Set(day.exercises.map((e) => e.exercise_id));
  const available = catalog.filter((e) => !usedIds.has(e.id));

  // Group available exercises by muscle group, preserving catalog order.
  const groups = new Map<string, ExerciseResponse[]>();
  for (const exercise of available) {
    const list = groups.get(exercise.muscle_group);
    if (list) {
      list.push(exercise);
    } else {
      groups.set(exercise.muscle_group, [exercise]);
    }
  }

  function handleSelect(event: ChangeEvent<HTMLSelectElement>) {
    const exerciseId = event.target.value;
    if (!exerciseId) return;
    event.target.value = '';
    addMutation.mutate(
      { day: day.day_of_week, exerciseId },
      { onSuccess: () => setPickerOpen(false) },
    );
  }

  function handleRemove(workoutExerciseId: string) {
    removeMutation.mutate({ day: day.day_of_week, workoutExerciseId });
  }

  return (
    <div className="rounded-card border border-border bg-surface p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-base text-text">
          {DAY_LABEL[day.day_of_week as keyof typeof DAY_LABEL] ??
            day.day_of_week}
        </h3>
        <button
          onClick={() => setPickerOpen((open) => !open)}
          className="inline-flex items-center gap-1 text-xs font-semibold text-accent bg-transparent border-none"
          style={{ minHeight: '28px', padding: '0 4px', cursor: 'pointer' }}
          aria-expanded={pickerOpen}
        >
          <Plus size={14} />
          Añadir ejercicio
        </button>
      </div>

      {pickerOpen && (
        <div className="mb-3">
          {catalogLoading ? (
            <p className="text-xs italic text-muted">Cargando ejercicios…</p>
          ) : catalogError ? (
            <p className="text-xs text-danger">
              No se pudo cargar el catálogo de ejercicios. Inténtalo de nuevo.
            </p>
          ) : available.length === 0 ? (
            <p className="text-xs italic text-muted">
              Todos los ejercicios ya están añadidos.
            </p>
          ) : (
            <select
              onChange={handleSelect}
              disabled={addMutation.isPending}
              defaultValue=""
              className="w-full text-sm rounded-input border border-border disabled:opacity-60"
              style={{ height: '40px', padding: '0 10px' }}
              aria-label="Selecciona un ejercicio"
            >
              <option value="" disabled>
                {addMutation.isPending ? 'Añadiendo…' : 'Selecciona un ejercicio'}
              </option>
              {[...groups.entries()].map(([muscleGroup, exercises]) => (
                <optgroup key={muscleGroup} label={muscleGroup}>
                  {exercises.map((exercise) => (
                    <option key={exercise.id} value={exercise.id}>
                      {exercise.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          )}
        </div>
      )}

      {addMutation.isError && (
        <p className="mb-2 text-xs text-danger">
          No se pudo añadir el ejercicio. Inténtalo de nuevo.
        </p>
      )}
      {removeMutation.isError && (
        <p className="mb-2 text-xs text-danger">
          No se pudo eliminar el ejercicio. Inténtalo de nuevo.
        </p>
      )}

      {day.exercises.length === 0 ? (
        <p className="text-sm italic text-muted">Sin ejercicios</p>
      ) : (
        <ol className="space-y-2">
          {day.exercises.map((ex) => {
            const exercise = exerciseById.get(ex.exercise_id);
            return (
              <li key={ex.id} className="flex items-center gap-2 text-sm">
                <span className="font-bold w-5 text-right shrink-0 text-accent">
                  {ex.order}.
                </span>
                {exercise ? (
                  <span className="flex-1 min-w-0">
                    <span className="text-text">{exercise.name}</span>
                    <span className="ml-2 text-xs text-muted">
                      {exercise.muscle_group}
                    </span>
                  </span>
                ) : (
                  <span className="flex-1 min-w-0 font-mono text-xs text-muted truncate">
                    {ex.exercise_id}
                  </span>
                )}
                <button
                  onClick={() => handleRemove(ex.id)}
                  disabled={removeMutation.isPending}
                  className="shrink-0 inline-flex items-center justify-center rounded text-danger bg-transparent border-none transition-colors hover:bg-danger hover:text-bg disabled:opacity-60"
                  style={{
                    minHeight: '28px',
                    height: '28px',
                    width: '28px',
                    cursor: 'pointer',
                  }}
                  aria-label="Quitar ejercicio"
                >
                  <X size={14} />
                </button>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}

export function WorkoutDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: workout, isLoading, isError, error } = useWorkout(id ?? '');
  const {
    data: exercises,
    isLoading: exercisesLoading,
    isError: exercisesError,
  } = useExercises();
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
            <TrainingDayCard
              key={day.day_of_week}
              workoutId={workout.id}
              day={day}
              catalog={exercises ?? []}
              catalogLoading={exercisesLoading}
              catalogError={exercisesError}
            />
          ))}
        </div>
      )}
    </div>
  );
}
