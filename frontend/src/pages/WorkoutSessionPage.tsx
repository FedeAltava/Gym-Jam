import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useWorkout } from '../hooks/useWorkouts';
import { useExercises } from '../hooks/useExercises';
import {
  useStartSession,
  useLogSet,
  useUpdateLog,
  useCompleteSession,
  useSessionsForDay,
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
  // Latest known log for this set — seeded from the session, then kept in
  // sync locally after log/update mutations succeed.
  const [log, setLog] = useState<ExerciseLogResponse | undefined>(existingLog);
  const [validationError, setValidationError] = useState<string | null>(null);
  const logSet = useLogSet();
  const updateLog = useUpdateLog();

  const isLogged = !!log;
  const isPending = logSet.isPending || updateLog.isPending;
  const isDisabled = sessionCompleted || isPending;
  const mutationError = logSet.error ?? updateLog.error;

  function handleLog() {
    const repsVal = parseInt(reps, 10);
    if (!reps || Number.isNaN(repsVal) || repsVal < 1) {
      setValidationError('Ingresa las repeticiones (mínimo 1).');
      return;
    }
    // A number input reports '' for invalid content, so `weight` can be empty
    // even when the placeholder makes it look filled. Never let NaN through:
    // JSON.stringify(NaN) serializes to null and the API rejects it (422).
    const weightVal = parseFloat(weight);
    if (weight === '' || !Number.isFinite(weightVal) || weightVal < 0) {
      setValidationError('Ingresa un peso válido en kg (0 o más).');
      return;
    }
    setValidationError(null);
    logSet.mutate(
      {
        sessionId,
        workoutExerciseId: exercise.id,
        setNumber,
        repsCompleted: repsVal,
        weightKg: weightVal,
        workoutId,
        dayId,
      },
      { onSuccess: (data) => setLog(data) },
    );
  }

  function handleUpdate() {
    if (!log) return;
    const repsVal = reps !== '' ? parseInt(reps, 10) : undefined;
    if (repsVal !== undefined && (Number.isNaN(repsVal) || repsVal < 1)) {
      setValidationError('Las repeticiones deben ser 1 o más.');
      return;
    }
    const weightVal = weight !== '' ? parseFloat(weight) : undefined;
    if (
      weightVal !== undefined &&
      (!Number.isFinite(weightVal) || weightVal < 0)
    ) {
      setValidationError('El peso debe ser un número de 0 o más kg.');
      return;
    }
    if (repsVal === undefined && weightVal === undefined) {
      setValidationError('Ingresa nuevas repeticiones o un nuevo peso.');
      return;
    }
    setValidationError(null);
    updateLog.mutate(
      {
        sessionId,
        logId: log.id,
        repsCompleted: repsVal,
        weightKg: weightVal,
        workoutId,
        dayId,
      },
      { onSuccess: (data) => setLog(data) },
    );
  }

  // Read-only summary once the session is completed.
  if (sessionCompleted && log) {
    return (
      <div
        className="flex items-center gap-3 py-2 px-3 rounded-btn"
        style={{ backgroundColor: 'rgba(0, 255, 135, 0.06)' }}
      >
        <span className="text-xs font-bold text-muted w-12 shrink-0">
          Serie {setNumber}
        </span>
        <span className="text-sm text-text flex-1">
          {log.reps_completed} reps
          {log.weight_kg != null && ` · ${log.weight_kg} kg`}
        </span>
        <CheckCircle2 size={16} className="text-accent shrink-0" />
      </div>
    );
  }

  const canSubmit = isLogged
    ? reps !== '' || weight !== ''
    : !!reps && weight !== '';

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
        placeholder={log ? String(log.reps_completed) : String(suggestedReps)}
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
        placeholder={
          log?.weight_kg != null
            ? String(log.weight_kg)
            : suggestedWeight != null
              ? String(suggestedWeight)
              : '0'
        }
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
        onClick={isLogged ? handleUpdate : handleLog}
        disabled={isDisabled || !canSubmit}
        className="text-xs font-semibold rounded-btn disabled:opacity-50"
        style={{
          height: '36px',
          padding: '0 12px',
          border: 'none',
          cursor: 'pointer',
          // Inline colors on purpose: Tailwind's content scanner can miss
          // dynamically-composed class strings and purge bg-orange-500 from
          // the production CSS. Inline styles cannot be purged.
          ...(isLogged
            ? { backgroundColor: '#f97316', color: '#fff' }
            : { backgroundColor: 'var(--neon-green)', color: 'var(--bg)' }),
        }}
      >
        {isPending ? '…' : isLogged ? 'Cambiar' : 'Registrar'}
      </button>
      {isLogged && (
        <CheckCircle2 size={16} className="text-accent shrink-0" />
      )}
      {validationError && (
        <span className="text-xs text-danger">{validationError}</span>
      )}
      {!validationError && (logSet.isError || updateLog.isError) && (
        <span className="text-xs text-danger">
          {(mutationError as Error).message}
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
  lastSessionLogs: Map<string, ExerciseLogResponse>;
  workoutId: string;
  dayId: string;
  sessionCompleted: boolean;
}

function ExerciseBlock({
  sessionId,
  exercise,
  exerciseName,
  logs,
  lastSessionLogs,
  workoutId,
  dayId,
  sessionCompleted,
}: ExerciseBlockProps) {
  const [extraSets, setExtraSets] = useState(0);
  const logsBySet = new Map(logs.map((l) => [l.set_number, l]));
  const totalSets = exercise.sets + extraSets;

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
        {Array.from({ length: totalSets }, (_, i) => i + 1).map(
          (setNum) => {
            const lastLog = lastSessionLogs.get(`${exercise.id}:${setNum}`);
            return (
              <SetRow
                key={setNum}
                sessionId={sessionId}
                exercise={exercise}
                exerciseName={exerciseName}
                setNumber={setNum}
                suggestedReps={lastLog?.reps_completed ?? exercise.reps_per_set}
                suggestedWeight={lastLog?.weight_kg ?? exercise.weight_kg}
                existingLog={logsBySet.get(setNum)}
                workoutId={workoutId}
                dayId={dayId}
                sessionCompleted={sessionCompleted}
              />
            );
          },
        )}
      </div>
      {!sessionCompleted && (
        <button
          onClick={() => setExtraSets((n) => n + 1)}
          className="mt-2 text-xs text-muted"
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
        >
          + Serie extra
        </button>
      )}
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

  // Existing sessions for this day — used to resume an in_progress session
  // instead of creating a zombie duplicate on every page visit.
  const { data: pastSessions, isLoading: sessionsLoading } = useSessionsForDay(
    workoutId,
    dayId,
  );

  // Active session held in local state — resumed from the backend if an
  // in_progress session exists, otherwise created on "Iniciar sesión".
  const [session, setSession] = useState<{
    id: string;
    status: 'in_progress' | 'completed';
    logs: import('../types/api').ExerciseLogResponse[];
  } | null>(null);

  // Seed local state from the fetched in_progress session (resume, not restart).
  useEffect(() => {
    if (session !== null || !pastSessions) return;
    const inProgress = pastSessions.find((s) => s.status === 'in_progress');
    if (inProgress) {
      setSession({
        id: inProgress.id,
        status: inProgress.status,
        logs: inProgress.logs,
      });
    }
  }, [pastSessions, session]);

  const hasInProgress =
    pastSessions?.some((s) => s.status === 'in_progress') ?? false;

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

  // Pre-fill placeholders from the most recent completed session for this
  // training day (any calendar date). Falls back to plan values if no history.
  const lastCompletedSession = (pastSessions ?? [])
    .filter((s) => s.status === 'completed')
    .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())[0];

  const lastSessionLogs = new Map(
    (lastCompletedSession?.logs ?? []).map((l) => [
      `${l.workout_exercise_id}:${l.set_number}`,
      l,
    ]),
  );

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

      {/* Loading existing sessions — don't offer "Iniciar" until we know
          whether there is an in_progress session to resume. */}
      {!session && sessionsLoading && <Spinner />}

      {/* Pre-start state — only when there is NO in_progress session */}
      {!session && !sessionsLoading && !hasInProgress && (
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
                  lastSessionLogs={lastSessionLogs}
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
