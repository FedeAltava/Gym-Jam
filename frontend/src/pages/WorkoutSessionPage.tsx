import { useState, useEffect, useCallback } from 'react';
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
  useDeleteExerciseLog,
} from '../hooks/useSessions';
import { useUserPreferences } from '../hooks/useUserPreferences';
import { Spinner } from '../components/Spinner';
import { DAY_LABEL } from '../lib/days';
import type {
  TrainingDayResponse,
  WorkoutExerciseResponse,
  ExerciseLogResponse,
} from '../types/api';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// ---------------------------------------------------------------------------
// Stepper
// ---------------------------------------------------------------------------

interface StepperProps {
  value: number;
  step: number;
  min: number;
  onChange: (v: number) => void;
  disabled?: boolean;
  'aria-label'?: string;
}

function Stepper({ value, step, min, onChange, disabled, 'aria-label': ariaLabel }: StepperProps) {
  function decrement() {
    onChange(Math.max(min, +(value - step).toFixed(4)));
  }
  function increment() {
    onChange(+(value + step).toFixed(4));
  }
  return (
    <div className="flex items-center gap-1" role="group" aria-label={ariaLabel}>
      <button
        type="button"
        onClick={decrement}
        disabled={disabled || value <= min}
        aria-label="Reducir"
        className="w-8 h-8 flex items-center justify-center rounded-btn bg-elevated border border-border text-text disabled:opacity-40 text-base font-bold leading-none"
      >
        −
      </button>
      <span className="w-14 text-center text-sm font-semibold text-text tabular-nums">
        {Number.isInteger(value) ? value : value.toFixed(1)}
      </span>
      <button
        type="button"
        onClick={increment}
        disabled={disabled}
        aria-label="Aumentar"
        className="w-8 h-8 flex items-center justify-center rounded-btn bg-elevated border border-border text-text disabled:opacity-40 text-base font-bold leading-none"
      >
        +
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Set row
// ---------------------------------------------------------------------------

interface SetRowProps {
  sessionId: string;
  exercise: WorkoutExerciseResponse;
  setNumber: number;
  suggestedReps: number;
  suggestedWeight: number | null;
  isBodyweight: boolean;
  existingLog: ExerciseLogResponse | undefined;
  workoutId: string;
  dayId: string;
  sessionCompleted: boolean;
  units: 'kg' | 'lb';
  onDoneSetsChange: (delta: number) => void;
}

function SetRow({
  sessionId,
  exercise,
  setNumber,
  suggestedReps,
  suggestedWeight,
  isBodyweight,
  existingLog,
  workoutId,
  dayId,
  sessionCompleted,
  units,
  onDoneSetsChange,
}: SetRowProps) {
  // Seed stepper values from existing log or suggestions.
  const [reps, setReps] = useState<number>(
    existingLog?.reps_completed ?? suggestedReps,
  );
  const [weight, setWeight] = useState<number>(
    existingLog?.weight_kg ?? suggestedWeight ?? 0,
  );
  // Latest known log for this set — seeded from the session, kept in sync locally.
  const [log, setLog] = useState<ExerciseLogResponse | undefined>(existingLog);

  const logSet = useLogSet();
  const updateLog = useUpdateLog();
  const deleteLog = useDeleteExerciseLog();

  const isLogged = !!log;
  const isPending = logSet.isPending || updateLog.isPending || deleteLog.isPending;
  const isDisabled = sessionCompleted || isPending;

  const weightStep = units === 'lb' ? 5 : 2.5;

  // Weight is stored always in kg (ADR 9). Display convert only for steppers.
  const displayWeight = units === 'lb' ? weight * 2.20462 : weight;
  const stepperDisplayWeight =
    units === 'lb' ? Math.round(displayWeight / 5) * 5 : weight;

  function toStorageKg(displayVal: number): number {
    return units === 'lb' ? displayVal / 2.20462 : displayVal;
  }

  // Read-only summary once the session is completed.
  if (sessionCompleted && log) {
    return (
      <div className="flex items-center gap-3 py-2 px-3 rounded-btn bg-accent/10">
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

  function handleToggleDone() {
    if (isLogged) {
      // Undo: delete the log
      const logId = log!.id;
      deleteLog.mutate(
        { sessionId, logId, workoutId, dayId },
        {
          onSuccess: () => {
            setLog(undefined);
            onDoneSetsChange(-1);
          },
        },
      );
    } else {
      // Mark done: post log with current stepper values
      const repsVal = Math.max(1, Math.round(reps));
      // NaN / negative guard — never let bad values through
      const weightKg: number | null = isBodyweight
        ? null
        : (() => {
            const kg = toStorageKg(weight);
            return Number.isFinite(kg) && kg >= 0 ? kg : 0;
          })();

      logSet.mutate(
        {
          sessionId,
          workoutExerciseId: exercise.id,
          setNumber,
          repsCompleted: repsVal,
          weightKg,
          workoutId,
          dayId,
        },
        {
          onSuccess: (data) => {
            setLog(data);
            onDoneSetsChange(+1);
          },
        },
      );
    }
  }

  function handleRepsChange(newReps: number) {
    setReps(newReps);
    // If already logged, PATCH immediately
    if (isLogged && log) {
      updateLog.mutate(
        {
          sessionId,
          logId: log.id,
          repsCompleted: Math.max(1, Math.round(newReps)),
          weightKg: undefined,
          workoutId,
          dayId,
        },
        { onSuccess: (data) => setLog(data) },
      );
    }
  }

  function handleWeightChange(newDisplayWeight: number) {
    const kg = toStorageKg(newDisplayWeight);
    setWeight(kg);
    // If already logged, PATCH immediately
    if (isLogged && log) {
      const weightKg = Number.isFinite(kg) && kg >= 0 ? kg : 0;
      updateLog.mutate(
        {
          sessionId,
          logId: log.id,
          repsCompleted: undefined,
          weightKg,
          workoutId,
          dayId,
        },
        { onSuccess: (data) => setLog(data) },
      );
    }
  }

  const doneClass = isLogged
    ? 'opacity-60 border-border-accent bg-card'
    : 'bg-card';

  return (
    <div
      className={`flex items-center gap-2 py-2 px-3 rounded-btn border border-border transition-colors ${doneClass}`}
    >
      <span className="text-xs font-bold text-muted w-14 shrink-0">
        Serie {setNumber}
      </span>

      <Stepper
        value={reps}
        step={1}
        min={0}
        onChange={handleRepsChange}
        disabled={isDisabled}
        aria-label={`Repeticiones, serie ${setNumber}`}
      />

      {!isBodyweight && (
        <Stepper
          value={stepperDisplayWeight}
          step={weightStep}
          min={0}
          onChange={handleWeightChange}
          disabled={isDisabled}
          aria-label={`Peso ${units}, serie ${setNumber}`}
        />
      )}
      {isBodyweight && (
        <span className="text-xs text-muted px-2">Peso corporal</span>
      )}

      {/* Done toggle */}
      <button
        type="button"
        onClick={handleToggleDone}
        disabled={isDisabled}
        aria-label={isLogged ? `Desmarcar serie ${setNumber}` : `Marcar serie ${setNumber} como hecha`}
        aria-pressed={isLogged}
        className={`ml-auto w-9 h-9 flex items-center justify-center rounded-btn border transition-colors disabled:opacity-40 ${
          isLogged
            ? 'bg-accent border-accent text-bg'
            : 'bg-elevated border-border text-muted'
        }`}
      >
        <CheckCircle2 size={18} />
      </button>

      {/* Mutation error */}
      {(logSet.isError || updateLog.isError || deleteLog.isError) && (
        <span className="text-xs text-danger ml-1">
          {((logSet.error ?? updateLog.error ?? deleteLog.error) as Error).message}
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
  muscleGroup: string;
  isBodyweight: boolean;
  logs: ExerciseLogResponse[];
  lastSessionLogs: Map<string, ExerciseLogResponse>;
  workoutId: string;
  dayId: string;
  sessionCompleted: boolean;
  units: 'kg' | 'lb';
  onDoneSetsChange: (delta: number) => void;
}

function ExerciseBlock({
  sessionId,
  exercise,
  exerciseName,
  muscleGroup,
  isBodyweight,
  logs,
  lastSessionLogs,
  workoutId,
  dayId,
  sessionCompleted,
  units,
  onDoneSetsChange,
}: ExerciseBlockProps) {
  const [extraSets, setExtraSets] = useState(0);
  const logsBySet = new Map(logs.map((l) => [l.set_number, l]));
  const totalSets = exercise.sets + extraSets;

  return (
    <div className="rounded-card border border-border bg-card p-4">
      <div className="mb-3">
        <h3 className="font-bold text-sm text-text">{exerciseName}</h3>
        <p className="text-xs text-muted mt-0.5">
          {muscleGroup && `${muscleGroup} · `}
          {exercise.sets} series · {exercise.reps_per_set} reps
        </p>
      </div>
      <div className="space-y-2">
        {Array.from({ length: totalSets }, (_, i) => i + 1).map((setNum) => {
          const lastLog = lastSessionLogs.get(`${exercise.id}:${setNum}`);
          return (
            <SetRow
              key={setNum}
              sessionId={sessionId}
              exercise={exercise}
              setNumber={setNum}
              suggestedReps={lastLog?.reps_completed ?? exercise.reps_per_set}
              suggestedWeight={lastLog?.weight_kg ?? exercise.weight_kg}
              isBodyweight={isBodyweight}
              existingLog={logsBySet.get(setNum)}
              workoutId={workoutId}
              dayId={dayId}
              sessionCompleted={sessionCompleted}
              units={units}
              onDoneSetsChange={onDoneSetsChange}
            />
          );
        })}
      </div>
      {!sessionCompleted && (
        <button
          type="button"
          onClick={() => setExtraSets((n) => n + 1)}
          className="mt-3 text-xs text-muted bg-transparent border-none cursor-pointer p-0"
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

  const { data: prefs } = useUserPreferences();
  const units = prefs?.units ?? 'kg';

  const startSession = useStartSession();
  const completeSession = useCompleteSession();

  // Existing sessions for this day — resume an in_progress session instead of
  // creating a zombie duplicate on every page visit.
  const { data: pastSessions, isLoading: sessionsLoading } = useSessionsForDay(
    workoutId,
    dayId,
  );

  // Tracks a session created during this page visit (after "Iniciar sesión").
  const [newSession, setNewSession] = useState<{
    id: string;
    status: 'in_progress' | 'completed';
    logs: ExerciseLogResponse[];
    started_at: string;
  } | null>(null);

  const inProgressFromHistory =
    pastSessions?.find((s) => s.status === 'in_progress') ?? null;

  const session = newSession;

  // Live timer — elapsed seconds since session.started_at
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!session) return;
    const startTime = new Date(session.started_at).getTime();
    // Initial value
    setElapsedSeconds(Math.floor((Date.now() - startTime) / 1000));
    const id = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [session]);

  // Done-sets counter — seeded from logs already in the session, then updated
  // via callbacks from SetRow as the user toggles sets.
  const [doneSets, setDoneSets] = useState(0);

  // Seed done count when session is first set
  useEffect(() => {
    if (session) {
      setDoneSets(session.logs.length);
    }
  }, [session?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDoneSetsChange = useCallback((delta: number) => {
    setDoneSets((prev) => Math.max(0, prev + delta));
  }, []);

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
          setNewSession({
            id: data.id,
            status: data.status,
            logs: data.logs,
            started_at: data.started_at,
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

  const sortedExercises = [...day.exercises].sort((a, b) => {
    const mgA = exerciseById.get(a.exercise_id)?.muscle_group ?? '';
    const mgB = exerciseById.get(b.exercise_id)?.muscle_group ?? '';
    const mg = mgA.localeCompare(mgB);
    return mg !== 0 ? mg : a.order - b.order;
  });

  // Pre-fill placeholders from the most recent completed session for this
  // training day (any calendar date). Falls back to plan values if no history.
  const lastCompletedSession = (pastSessions ?? [])
    .filter((s) => s.status === 'completed')
    .sort(
      (a, b) =>
        new Date(b.started_at).getTime() - new Date(a.started_at).getTime(),
    )[0];

  const lastSessionLogs = new Map(
    (lastCompletedSession?.logs ?? []).map((l) => [
      `${l.workout_exercise_id}:${l.set_number}`,
      l,
    ]),
  );

  // Progress bar stats
  const totalSets = sortedExercises.reduce((sum, ex) => sum + ex.sets, 0);
  const progressPct = totalSets > 0 ? Math.min(100, (doneSets / totalSets) * 100) : 0;

  return (
    <div>
      <Link
        to={`/workouts/${workoutId}`}
        className="inline-flex items-center gap-1.5 text-sm font-semibold mb-5 text-muted no-underline"
      >
        <ArrowLeft size={16} /> Volver al entrenamiento
      </Link>

      <div className="mb-4 flex items-start justify-between">
        <div>
          <h1 className="font-bold text-2xl text-text">{workout.name}</h1>
          <p className="text-sm text-muted mt-1">{dayLabel}</p>
        </div>
        {session && (
          <div
            className="text-right"
            aria-label="Tiempo transcurrido"
          >
            <span className="font-condensed font-bold text-xl text-accent tabular-nums">
              {formatElapsed(elapsedSeconds)}
            </span>
          </div>
        )}
      </div>

      {/* Progress bar — only while session is active */}
      {session && (
        <div className="mb-6">
          <div className="flex justify-between text-xs text-muted mb-1.5">
            <span>Progreso</span>
            <span>
              {doneSets}/{totalSets} series
            </span>
          </div>
          <div
            className="h-2 rounded-btn bg-elevated overflow-hidden"
            role="progressbar"
            aria-valuenow={doneSets}
            aria-valuemin={0}
            aria-valuemax={totalSets}
          >
            <div
              className="h-full bg-accent rounded-btn transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      )}

      {/* Loading existing sessions */}
      {!session && sessionsLoading && <Spinner />}

      {/* Resume confirmation */}
      {!newSession && inProgressFromHistory && !sessionsLoading && (
        <div
          className="rounded-card border border-border bg-surface p-4 mb-4"
          role="alert"
        >
          <p className="text-sm font-semibold text-text mb-1">
            Sesión en progreso del{' '}
            {new Date(inProgressFromHistory.started_at).toLocaleDateString(
              'es',
              { day: 'numeric', month: 'short', year: 'numeric' },
            )}
          </p>
          <p className="text-xs text-muted mb-3">
            ¿Deseas retomarla o iniciar una nueva sesión?
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() =>
                setNewSession({
                  id: inProgressFromHistory.id,
                  status: inProgressFromHistory.status,
                  logs: inProgressFromHistory.logs,
                  started_at: inProgressFromHistory.started_at,
                })
              }
              className="text-sm font-semibold rounded-btn bg-accent text-bg border-none cursor-pointer px-4 h-9"
            >
              Retomar
            </button>
            <button
              type="button"
              onClick={handleStart}
              disabled={startSession.isPending}
              className="text-sm font-semibold rounded-btn bg-transparent border border-border text-text cursor-pointer px-4 h-9 disabled:opacity-60"
            >
              {startSession.isPending ? 'Iniciando…' : 'Nueva sesión'}
            </button>
          </div>
          {startSession.isError && (
            <p className="mt-2 text-xs text-danger">
              {(startSession.error as Error).message}
            </p>
          )}
        </div>
      )}

      {/* Pre-start state */}
      {!newSession && !sessionsLoading && !inProgressFromHistory && (
        <div className="rounded-card border-2 border-dashed border-border p-8 text-center">
          <p className="text-sm text-muted mb-4">
            {day.exercises.length === 0
              ? 'Este día no tiene ejercicios configurados.'
              : `${day.exercises.length} ejercicio${day.exercises.length !== 1 ? 's' : ''} planificado${day.exercises.length !== 1 ? 's' : ''}`}
          </p>
          {day.exercises.length > 0 && (
            <>
              <button
                type="button"
                onClick={handleStart}
                disabled={startSession.isPending}
                className="font-semibold rounded-btn bg-accent text-bg border-none cursor-pointer px-8 h-12 text-base disabled:opacity-60 neon-glow"
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
              const catalogExercise = exerciseById.get(exercise.exercise_id);
              return (
                <ExerciseBlock
                  key={exercise.id}
                  sessionId={session.id}
                  exercise={exercise}
                  exerciseName={catalogExercise?.name ?? exercise.exercise_id}
                  muscleGroup={catalogExercise?.muscle_group ?? ''}
                  isBodyweight={catalogExercise?.is_bodyweight ?? false}
                  logs={exerciseLogs}
                  lastSessionLogs={lastSessionLogs}
                  workoutId={workoutId}
                  dayId={dayId}
                  sessionCompleted={session.status === 'completed'}
                  units={units}
                  onDoneSetsChange={handleDoneSetsChange}
                />
              );
            })}
          </div>

          {session.status === 'in_progress' && (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleComplete}
                disabled={completeSession.isPending}
                className="font-semibold rounded-btn bg-accent text-bg border-none cursor-pointer px-8 h-12 text-base disabled:opacity-60 neon-glow"
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
