import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, X, Play, ChevronDown, ChevronUp, Pencil, Trash2 } from 'lucide-react';
import { useWorkout, useDeleteWorkout, useReorderTrainingDays, useRenameWorkout, useSetWorkoutActive, useAddTrainingDay, useRemoveTrainingDay } from '../hooks/useWorkouts';
import { useExercises, useRemoveExercise } from '../hooks/useExercises';
import {
  useSessionsForDay,
  useCompleteSession,
  useDeleteSession,
} from '../hooks/useSessions';
import { Spinner } from '../components/Spinner';
import { DAY_LABEL, DAYS } from '../lib/days';
import type { ExerciseResponse, TrainingDayResponse } from '../types/api';

interface TrainingDayCardProps {
  workoutId: string;
  day: TrainingDayResponse;
  allDays: TrainingDayResponse[];
  catalog: ExerciseResponse[];
  catalogLoading: boolean;
  catalogError: boolean;
  onReorder: (orderedIds: string[]) => void;
  reorderPending: boolean;
  onDelete: (dayOfWeek: string) => void;
}

function PastSessionsList({
  workoutId,
  dayId,
}: {
  workoutId: string;
  dayId: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const { data: sessions, isLoading, isError } = useSessionsForDay(workoutId, dayId);
  const completeSession = useCompleteSession();
  const deleteSession = useDeleteSession();

  if (isLoading) {
    return <p className="text-xs italic text-muted mt-3">Cargando sesiones…</p>;
  }
  if (isError) {
    return (
      <p className="text-xs text-danger mt-3">
        No se pudieron cargar las sesiones anteriores.
      </p>
    );
  }
  if (!sessions || sessions.length === 0) {
    return (
      <p className="text-xs italic text-muted mt-3">Sin sesiones anteriores.</p>
    );
  }

  return (
    <div className="mt-3 border-t border-border pt-3">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="inline-flex items-center gap-1 text-xs font-semibold text-muted bg-transparent border-none"
        style={{ cursor: 'pointer', padding: 0 }}
      >
        {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        {sessions.length} sesión{sessions.length !== 1 ? 'es' : ''} anterior{sessions.length !== 1 ? 'es' : ''}
      </button>
      {expanded && (
        <ul className="mt-2 space-y-1">
          {sessions.map((s) => (
            <li key={s.id} className="flex items-center gap-2 text-xs">
              <span className="text-muted">
                {new Date(s.started_at).toLocaleDateString('es', {
                  day: '2-digit',
                  month: 'short',
                  year: 'numeric',
                })}
              </span>
              <span
                className="px-1.5 py-0.5 rounded-full text-xs font-semibold"
                style={
                  s.status === 'completed'
                    ? {
                        backgroundColor: 'rgba(0, 255, 135, 0.1)',
                        color: 'var(--neon-green)',
                        border: '1px solid rgba(0, 255, 135, 0.3)',
                      }
                    : {
                        backgroundColor: 'rgba(0, 212, 255, 0.1)',
                        color: 'var(--neon-blue)',
                        border: '1px solid rgba(0, 212, 255, 0.3)',
                      }
                }
              >
                {s.status === 'completed' ? 'completada' : 'en progreso'}
              </span>
              {s.status === 'in_progress' && (
                <span className="inline-flex items-center gap-1.5">
                  {s.logs.length > 0 && (
                    <button
                      onClick={() =>
                        completeSession.mutate({ sessionId: s.id, workoutId, dayId })
                      }
                      disabled={completeSession.isPending || deleteSession.isPending}
                      className="px-1.5 py-0.5 rounded-full text-xs font-semibold leading-4 disabled:opacity-60"
                      style={{
                        border: 'none',
                        cursor: 'pointer',
                        backgroundColor: 'var(--neon-green)',
                        color: 'var(--bg)',
                      }}
                    >
                      {completeSession.isPending &&
                      completeSession.variables?.sessionId === s.id
                        ? '…'
                        : 'Completar'}
                    </button>
                  )}
                  <button
                    onClick={() =>
                      deleteSession.mutate({ sessionId: s.id, workoutId, dayId })
                    }
                    disabled={completeSession.isPending || deleteSession.isPending}
                    className="px-1.5 py-0.5 rounded-full text-xs font-semibold leading-4 disabled:opacity-60"
                    style={{
                      border: 'none',
                      cursor: 'pointer',
                      backgroundColor: '#ef4444',
                      color: '#fff',
                    }}
                  >
                    {deleteSession.isPending &&
                    deleteSession.variables?.sessionId === s.id
                      ? '…'
                      : 'Eliminar'}
                  </button>
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function TrainingDayCard({
  workoutId,
  day,
  allDays,
  catalog,
  onReorder,
  reorderPending,
  onDelete,
}: TrainingDayCardProps) {
  const removeMutation = useRemoveExercise(workoutId);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const sortedDays = [...allDays].sort((a, b) => a.order - b.order);
  const currentIndex = sortedDays.findIndex((d) => d.id === day.id);
  const canMoveUp = currentIndex > 0;
  const canMoveDown = currentIndex < sortedDays.length - 1;

  function handleMoveUp() {
    if (!canMoveUp) return;
    const newOrder = [...sortedDays];
    [newOrder[currentIndex - 1], newOrder[currentIndex]] = [
      newOrder[currentIndex],
      newOrder[currentIndex - 1],
    ];
    onReorder(newOrder.map((d) => d.id));
  }

  function handleMoveDown() {
    if (!canMoveDown) return;
    const newOrder = [...sortedDays];
    [newOrder[currentIndex], newOrder[currentIndex + 1]] = [
      newOrder[currentIndex + 1],
      newOrder[currentIndex],
    ];
    onReorder(newOrder.map((d) => d.id));
  }

  const exerciseById = new Map(catalog.map((e) => [e.id, e]));

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
        <div className="flex items-center gap-2">
          <button
            onClick={handleMoveUp}
            disabled={!canMoveUp || reorderPending}
            className="inline-flex items-center justify-center rounded text-muted bg-transparent border-none transition-colors hover:text-text disabled:opacity-30"
            style={{ minHeight: '28px', height: '28px', width: '28px', cursor: canMoveUp ? 'pointer' : 'default' }}
            aria-label="Mover día arriba"
          >
            <ChevronUp size={14} />
          </button>
          <button
            onClick={handleMoveDown}
            disabled={!canMoveDown || reorderPending}
            className="inline-flex items-center justify-center rounded text-muted bg-transparent border-none transition-colors hover:text-text disabled:opacity-30"
            style={{ minHeight: '28px', height: '28px', width: '28px', cursor: canMoveDown ? 'pointer' : 'default' }}
            aria-label="Mover día abajo"
          >
            <ChevronDown size={14} />
          </button>
          {day.id && (
            <Link
              to={`/workouts/${workoutId}/session/${day.id}`}
              className="inline-flex items-center gap-1 text-xs font-semibold text-info no-underline bg-transparent border-none"
              style={{ minHeight: '28px', padding: '0 4px' }}
              aria-label="Iniciar sesión"
            >
              <Play size={13} />
              <span className="sm:hidden">Iniciar</span>
            </Link>
          )}
          <Link
            to={`/workouts/${workoutId}/days/${day.day_of_week}/add-exercises`}
            className="inline-flex items-center gap-1 text-xs font-semibold text-accent no-underline bg-transparent"
            style={{ minHeight: '28px', padding: '0 4px' }}
            aria-label="Añadir ejercicios"
          >
            <Plus size={14} />
            <span className="sm:hidden">Añadir</span>
          </Link>
          <button
            onClick={() => setConfirmingDelete(true)}
            className="inline-flex items-center justify-center rounded text-danger bg-transparent border-none transition-colors hover:bg-danger hover:text-bg"
            style={{ minHeight: '28px', height: '28px', width: '28px', cursor: 'pointer' }}
            aria-label="Eliminar día"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {confirmingDelete && (
        <div className="mb-3 p-3 rounded border border-danger text-sm">
          <p className="text-text mb-2">
            ¿Eliminar este día? Se perderán todas las sesiones registradas permanentemente.
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onDelete(day.day_of_week)}
              className="text-xs font-semibold rounded-btn bg-danger text-bg"
              style={{ height: '28px', padding: '0 10px', border: 'none', cursor: 'pointer' }}
            >
              Sí, eliminar
            </button>
            <button
              onClick={() => setConfirmingDelete(false)}
              className="text-xs font-semibold rounded-btn border border-border text-muted"
              style={{ height: '28px', padding: '0 10px', backgroundColor: 'transparent', cursor: 'pointer' }}
            >
              Cancelar
            </button>
          </div>
        </div>
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

      {day.id && (
        <PastSessionsList workoutId={workoutId} dayId={day.id} />
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
  const reorderDaysMutation = useReorderTrainingDays(id ?? '');
  const renameMutation = useRenameWorkout(id ?? '');
  const setActiveMutation = useSetWorkoutActive(id ?? '');
  const addDayMutation = useAddTrainingDay(id ?? '');
  const removeDayMutation = useRemoveTrainingDay(id ?? '');
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [showDayPicker, setShowDayPicker] = useState(false);

  // Rename state
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [renameError, setRenameError] = useState<string | null>(null);
  const renameInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isRenaming && renameInputRef.current) {
      renameInputRef.current.focus();
      renameInputRef.current.select();
    }
  }, [isRenaming]);

  function startRename() {
    setRenameValue(workout?.name ?? '');
    setRenameError(null);
    setIsRenaming(true);
  }

  function cancelRename() {
    setIsRenaming(false);
    setRenameError(null);
  }

  function commitRename() {
    if (!id || renameMutation.isPending) return;
    const trimmed = renameValue.trim();
    if (!trimmed) {
      setRenameError('El nombre no puede estar vacío.');
      return;
    }
    setRenameError(null);
    renameMutation.mutate(trimmed, {
      onSuccess: () => setIsRenaming(false),
      onError: () => setRenameError('No se pudo renombrar. Inténtalo de nuevo.'),
    });
  }

  function handleRenameKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') commitRename();
    if (e.key === 'Escape') cancelRename();
  }

  if (isLoading) return <Spinner />;
  if (isError)
    return (
      <p className="text-sm text-danger">Error: {(error as Error).message}</p>
    );
  if (!workout) return null;

  const availableDays = DAYS
    .filter((d) => !workout.training_days.some((td) => td.day_of_week === d))
    .map((d) => ({ value: d, label: DAY_LABEL[d] }));

  function handleDelete() {
    if (!id) return;
    deleteMutation.mutate(id, {
      onSuccess: () => navigate('/dashboard'),
    });
  }

  function handleAddDay(dayValue: string) {
    addDayMutation.mutate(dayValue, {
      onSuccess: () => setShowDayPicker(false),
    });
  }

  function handleRemoveDay(dayOfWeek: string) {
    removeDayMutation.mutate(dayOfWeek);
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
          {isRenaming ? (
            <div className="flex items-center gap-2 flex-wrap">
              <input
                ref={renameInputRef}
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onKeyDown={handleRenameKeyDown}
                disabled={renameMutation.isPending}
                className="font-bold text-2xl text-text rounded-input border border-border bg-bg-elevated"
                style={{ padding: '2px 8px', minWidth: '0', flex: '1 1 0' }}
                aria-label="Nuevo nombre del entrenamiento"
              />
              <button
                onClick={commitRename}
                disabled={renameMutation.isPending}
                className="text-sm font-semibold rounded-btn bg-accent text-bg disabled:opacity-60"
                style={{ height: '32px', padding: '0 10px', border: 'none', cursor: 'pointer', color: 'var(--bg)', backgroundColor: 'var(--neon-green)' }}
              >
                {renameMutation.isPending ? '…' : 'Guardar'}
              </button>
              <button
                onClick={cancelRename}
                disabled={renameMutation.isPending}
                className="text-sm font-semibold rounded-btn border border-border text-muted"
                style={{ height: '32px', padding: '0 10px', backgroundColor: 'transparent', cursor: 'pointer' }}
              >
                Cancelar
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="font-bold text-2xl text-text">{workout.name}</h1>
              <button
                onClick={startRename}
                className="inline-flex items-center justify-center rounded text-muted bg-transparent border-none transition-colors hover:text-text"
                style={{ minHeight: '28px', height: '28px', width: '28px', cursor: 'pointer' }}
                aria-label="Renombrar entrenamiento"
              >
                <Pencil size={15} />
              </button>
              <button
                onClick={() => setActiveMutation.mutate(!workout.is_active)}
                disabled={setActiveMutation.isPending}
                className="text-xs font-semibold px-2 py-0.5 rounded-full transition-opacity hover:opacity-80 disabled:opacity-50"
                style={
                  workout.is_active
                    ? {
                        backgroundColor: 'rgba(0, 255, 135, 0.1)',
                        border: '1px solid rgba(0, 255, 135, 0.3)',
                        color: 'var(--color-accent)',
                        cursor: 'pointer',
                      }
                    : {
                        backgroundColor: 'rgba(128, 128, 128, 0.1)',
                        border: '1px solid rgba(128, 128, 128, 0.3)',
                        color: 'var(--color-muted)',
                        cursor: 'pointer',
                      }
                }
                aria-label={workout.is_active ? 'Desactivar entrenamiento' : 'Activar entrenamiento'}
              >
                {workout.is_active ? 'Activo' : 'Inactivo'}
              </button>
            </div>
          )}
          {renameError && (
            <p className="text-xs text-danger mt-1">{renameError}</p>
          )}
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
        <div className="py-16 rounded-card border-2 border-dashed border-border px-4">
          <p className="text-sm italic text-muted text-center mb-4">
            Sin días de entrenamiento configurados.
          </p>
          {availableDays.length > 0 && (
            <div className="flex flex-wrap gap-2 justify-center">
              {availableDays.map((d) => (
                <button
                  key={d.value}
                  onClick={() => handleAddDay(d.value)}
                  disabled={addDayMutation.isPending}
                  className="text-xs font-semibold rounded-full border border-border text-muted transition-colors hover:border-accent hover:text-accent disabled:opacity-60"
                  style={{ height: '28px', padding: '0 12px', backgroundColor: 'transparent', cursor: 'pointer' }}
                >
                  {d.label}
                </button>
              ))}
            </div>
          )}
          {addDayMutation.isError && (
            <p className="mt-2 text-xs text-danger text-center">
              {(addDayMutation.error as Error).message}
            </p>
          )}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {workout.training_days.map((day) => (
            <TrainingDayCard
              key={day.day_of_week}
              workoutId={workout.id}
              day={day}
              allDays={workout.training_days}
              catalog={exercises ?? []}
              catalogLoading={exercisesLoading}
              catalogError={exercisesError}
              onReorder={(orderedIds) => reorderDaysMutation.mutate({ orderedDayIds: orderedIds })}
              reorderPending={reorderDaysMutation.isPending}
              onDelete={handleRemoveDay}
            />
          ))}
        </div>
      )}

      {removeDayMutation.isError && (
        <p className="mt-3 text-xs text-danger">
          {(removeDayMutation.error as Error).message.includes('exercise')
            ? 'Elimina todos los ejercicios de este día antes de eliminarlo.'
            : (removeDayMutation.error as Error).message}
        </p>
      )}

      {workout.training_days.length > 0 && availableDays.length > 0 && (
        <div className="mt-4">
          {!showDayPicker ? (
            <button
              onClick={() => setShowDayPicker(true)}
              className="text-sm font-semibold text-muted bg-transparent border-none transition-colors hover:text-accent"
              style={{ cursor: 'pointer', padding: '4px 0' }}
            >
              + Agregar día
            </button>
          ) : (
            <div>
              <div className="flex flex-wrap gap-2 items-center">
                {availableDays.map((d) => (
                  <button
                    key={d.value}
                    onClick={() => handleAddDay(d.value)}
                    disabled={addDayMutation.isPending}
                    className="text-xs font-semibold rounded-full border border-border text-muted transition-colors hover:border-accent hover:text-accent disabled:opacity-60"
                    style={{ height: '28px', padding: '0 12px', backgroundColor: 'transparent', cursor: 'pointer' }}
                  >
                    {d.label}
                  </button>
                ))}
                <button
                  onClick={() => setShowDayPicker(false)}
                  className="text-xs font-semibold text-muted bg-transparent border-none transition-colors hover:text-text"
                  style={{ cursor: 'pointer', padding: '4px 6px' }}
                >
                  Cancelar
                </button>
              </div>
              {addDayMutation.isError && (
                <p className="mt-2 text-xs text-danger">
                  {(addDayMutation.error as Error).message}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
