import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useWorkout } from '../hooks/useWorkouts';
import { useExercises } from '../hooks/useExercises';
import {
  useStartSession,
  useLogSet,
  useCompleteSession,
} from '../hooks/useSessions';
import { Spinner } from '../components/Spinner';
import { DAY_LABEL } from '../lib/days';
import type {
  TrainingDayResponse,
  WorkoutExerciseResponse,
  ExerciseLogResponse,
} from '../types/api';

// ---------------------------------------------------------------------------
// Set row
// ---------------------------------------------------------------------------

interface SetRowProps {
  sessionId: string;
  exercise: WorkoutExerciseResponse;
  exerciseName: string;
  setNumber: number;
  suggestedReps: number;
  suggestedWeight: number | null;
  existingLog: ExerciseLogResponse | undefined;
  workoutId: string;
  dayId: string;
  sessionCompleted: boolean;
}

function SetRow({
  sessionId,
  exercise,
  exerciseName: _exerciseName,
  setNumber,
  suggestedReps,
  suggestedWeight,
  existingLog,
  workoutId,
  dayId,
  sessionCompleted,
}: SetRowProps) {
  const [reps, setReps] = useState('');
  const [weight, setWeight] = useState('');
  const logSet = useLogSet();

  const isLogged = !!existingLog;
  const isDisabled = isLogged || sessionCompleted || logSet.isPending;

  function handleLog() {
    const repsVal = parseInt(reps, 10);
    if (!reps || isNaN(repsVal) || repsVal < 1) return;
    const weightVal = weight !== '' ? parseFloat(weight) : null;
    logSet.mutate({
      sessionId,
      workoutExerciseId: exercise.id,
      setNumber,
      repsCompleted: repsVal,
      weightKg: weightVal,
      workoutId,
      dayId,
    });
  }

  if (isLogged && existingLog) {
    return (
      <div
        className="flex items-center gap-3 py-2 px-3 rounded-btn"
        style={{ backgroundColor: 'rgba(0, 255, 135, 0.06)' }}
      >
        <span className="text-xs font-bold text-muted w-12 shrink-0">
          Serie {setNumber}
        </span>
        <span className="text-sm text-text flex-1">
          {existingLog.reps_completed} reps
          {existingLog.weight_kg != null && ` · ${existingLog.weight_kg} kg`}
        </span>
        <CheckCircle2 size={16} className="text-accent shrink-0" />
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 py-1.5">
      <span className="text-xs font-bold text-muted w-12 shrink-0">
        Serie {setNumber}
      </span>
      <input
        type="number"
        min={1}
        value={reps}
        onChange={(e) => setReps(e.target.value)}
        placeholder={String(suggestedReps)}
        disabled={isDisabled}
        aria-label={`Repeticiones, serie ${setNumber}`}
        className="w-20 text-sm disabled:opacity-50"
        style={{
          height: '36px',
          borderRadius: '8px',
          border: '1px solid var(--border)',
          padding: '0 8px',
          backgroundColor: 'var(--bg-elevated)',
          color: 'var(--text)',
        }}
      />
      <input
        type="number"
        min={0}
        step={0.5}
        value={weight}
        onChange={(e) => setWeight(e.target.value)}
        placeholder={suggestedWeight != null ? String(suggestedWeight) : '—'}
        disabled={isDisabled}
        aria-label={`Peso kg, serie ${setNumber}`}
        className="w-20 text-sm disabled:opacity-50"
        style={{
          height: '36px',
          borderRadius: '8px',
          border: '1px solid var(--border)',
          padding: '0 8px',
          backgroundColor: 'var(--bg-elevated)',
          color: 'var(--text)',
        }}
      />
      <button
        onClick={handleLog}
        disabled={isDisabled || !reps}
        className="text-xs font-semibold rounded-btn disabled:opacity-50"
        style={{
          height: '36px',
          padding: '0 12px',
          border: 'none',
          backgroundColor: 'var(--neon-green)',
          color: 'var(--bg)',
          cursor: 'pointer',
        }}
      >
        {logSet.isPending ? '…' : 'Registrar'}
      </button>
      {logSet.isError && (
        <span className="text-xs text-danger">
          {(logSet.error as Error).message}
        </span>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Exercise block
// ---------------------------------------------------------------------------

interface ExerciseBlockProps {
  sessionId: string;
  exercise: WorkoutExerciseResponse;
  exerciseName: string;
  logs: ExerciseLogResponse[];
  workoutId: string;
  dayId: string;
  sessionCompleted: boolean;
}

function ExerciseBlock({
  sessionId,
  exercise,
  exerciseName,
  logs,
  workoutId,
  dayId,
  sessionCompleted,
}: ExerciseBlockProps) {
  const logsBySet = new Map(logs.map((l) => [l.set_number, l]));

  return (
    <div className="rounded-card border border-border bg-surface p-4">
      <div className="mb-3">
        <h3 className="font-bold text-sm text-text">{exerciseName}</h3>
        <p className="text-xs text-muted mt-0.5">
          {exercise.sets} series · {exercise.reps_per_set} reps
          {exercise.weight_kg != null && ` · ${exercise.weight_kg} kg sugerido`}
        </p>
      </div>
      <div className="space-y-1">
        {Array.from({ length: exercise.sets }, (_, i) => i + 1).map(
          (setNum) => (
            <SetRow
              key={setNum}
              sessionId={sessionId}
              exercise={exercise}
              exerciseName={exerciseName}
              setNumber={setNum}
              suggestedReps={exercise.reps_per_set}
              suggestedWeight={exercise.weight_kg}
              existingLog={logsBySet.get(setNum)}
              workoutId={workoutId}
              dayId={dayId}
              sessionCompleted={sessionCompleted}
            />
          ),
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function WorkoutSessionPage() {
  const { workoutId = '', dayId = '' } = useParams<{
    workoutId: string;
    dayId: string;
  }>();
  const navigate = useNavigate();

  const {
    data: workout,
    isLoading: workoutLoading,
    isError: workoutError,
  } = useWorkout(workoutId);

  const { data: exercises } = useExercises();
  const exerciseById = new Map((exercises ?? []).map((e) => [e.id, e]));

  const startSession = useStartSession();
  const completeSession = useCompleteSession();

  // Active session held in local state — created once per page visit.
  const [session, setSession] = useState<{
    id: string;
    status: 'in_progress' | 'completed';
    logs: import('../types/api').ExerciseLogResponse[];
  } | null>(null);

  if (workoutLoading) return <Spinner />;
  if (workoutError || !workout)
    return (
      <p className="text-sm text-danger">
        No se pudo cargar el entrenamiento.
      </p>
    );

  const day: TrainingDayResponse | undefined = workout.training_days.find(
    (d) => d.id === dayId,
  );

  if (!day) {
    return (
      <p className="text-sm text-danger">
        Día de entrenamiento no encontrado.
      </p>
    );
  }

  const dayLabel =
    DAY_LABEL[day.day_of_week as keyof typeof DAY_LABEL] ?? day.day_of_week;

  function handleStart() {
    startSession.mutate(
      { workoutId, dayId },
      {
        onSuccess: (data) => {
          setSession({
            id: data.id,
            status: data.status,
            logs: data.logs,
          });
        },
      },
    );
  }

  function handleComplete() {
    if (!session) return;
    completeSession.mutate(
      { sessionId: session.id, workoutId, dayId },
      {
        onSuccess: () => {
          navigate(`/workouts/${workoutId}`);
        },
      },
    );
  }

  // Build a stable exercise-name lookup from the workout catalog query.
  // The catalog hook (useExercises) is not needed here — exercise names are
  // not included in WorkoutExerciseResponse. We show the exercise id as
  // fallback and order by `order` field.
  const sortedExercises = [...day.exercises].sort((a, b) => a.order - b.order);

  return (
    <div>
      <Link
        to={`/workouts/${workoutId}`}
        className="inline-flex items-center gap-1.5 text-sm font-semibold mb-5 text-muted no-underline"
      >
        <ArrowLeft size={16} /> Volver al entrenamiento
      </Link>

      <div className="mb-6">
        <h1 className="font-bold text-2xl text-text">{workout.name}</h1>
        <p className="text-sm text-muted mt-1">{dayLabel}</p>
      </div>

      {/* Pre-start state */}
      {!session && (
        <div className="rounded-card border-2 border-dashed border-border p-8 text-center">
          <p className="text-sm text-muted mb-4">
            {day.exercises.length === 0
              ? 'Este día no tiene ejercicios configurados.'
              : `${day.exercises.length} ejercicio${day.exercises.length !== 1 ? 's' : ''} planificado${day.exercises.length !== 1 ? 's' : ''}`}
          </p>
          {day.exercises.length > 0 && (
            <>
              <button
                onClick={handleStart}
                disabled={startSession.isPending}
                className="font-semibold rounded-btn disabled:opacity-60"
                style={{
                  height: '48px',
                  padding: '0 32px',
                  border: 'none',
                  backgroundColor: 'var(--neon-green)',
                  color: 'var(--bg)',
                  fontSize: '15px',
                  cursor: 'pointer',
                  boxShadow: '0 0 16px rgba(0, 255, 135, 0.4)',
                }}
              >
                {startSession.isPending ? 'Iniciando…' : 'Iniciar sesión'}
              </button>
              {startSession.isError && (
                <p className="mt-3 text-xs text-danger">
                  {(startSession.error as Error).message}
                </p>
              )}
            </>
          )}
        </div>
      )}

      {/* Active session */}
      {session && (
        <>
          <div className="space-y-4 mb-6">
            {sortedExercises.map((exercise) => {
              const exerciseLogs = session.logs.filter(
                (l) => l.workout_exercise_id === exercise.id,
              );
              return (
                <ExerciseBlock
                  key={exercise.id}
                  sessionId={session.id}
                  exercise={exercise}
                  exerciseName={exerciseById.get(exercise.exercise_id)?.name ?? exercise.exercise_id}
                  logs={exerciseLogs}
                  workoutId={workoutId}
                  dayId={dayId}
                  sessionCompleted={session.status === 'completed'}
                />
              );
            })}
          </div>

          {session.status === 'in_progress' && (
            <div className="flex justify-end">
              <button
                onClick={handleComplete}
                disabled={completeSession.isPending}
                className="font-semibold rounded-btn disabled:opacity-60"
                style={{
                  height: '48px',
                  padding: '0 32px',
                  border: 'none',
                  backgroundColor: 'var(--neon-green)',
                  color: 'var(--bg)',
                  fontSize: '15px',
                  cursor: 'pointer',
                  boxShadow: '0 0 16px rgba(0, 255, 135, 0.4)',
                }}
              >
                {completeSession.isPending ? 'Completando…' : 'Completar sesión'}
              </button>
            </div>
          )}
          {completeSession.isError && (
            <p className="mt-3 text-xs text-danger text-right">
              {(completeSession.error as Error).message}
            </p>
          )}
        </>
      )}
    </div>
  );
}
