import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeftRight, CheckCircle2 } from 'lucide-react';
import { useWorkout } from '../hooks/useWorkouts';
import { useExercises, useLastSets } from '../hooks/useExercises';
import {
  useStartSession,
  useLogSet,
  useUpdateLog,
  useCompleteSession,
  useSessionsForDay,
  useDeleteExerciseLog,
  useDeleteSession,
  useSwapExercise,
  useUndoExerciseSwap,
} from '../hooks/useSessions';
import { Spinner } from '../components/Spinner';
import { MainExerciseBadge } from '../components/MainExerciseBadge';
import { ExerciseSwapSheet } from '../components/sessions/ExerciseSwapSheet';
import { ApiError } from '../lib/api';
import { DAY_LABEL } from '../lib/days';
import { machineTwin } from '../lib/machineVariants';
import type {
  TrainingDayResponse,
  WorkoutExerciseResponse,
  ExerciseLogResponse,
  ExerciseSwapResponse,
  LastSetResponse,
} from '../types/api';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

/** Catalog exercise actually done in a planned slot: its swap, else the plan. */
function doneExerciseId(
  swaps: ExerciseSwapResponse[] | undefined,
  exercise: WorkoutExerciseResponse,
): string {
  return swaps?.find((s) => s.workout_exercise_id === exercise.id)?.exercise_id ?? exercise.exercise_id;
}

// ---------------------------------------------------------------------------
// Numeric input
// ---------------------------------------------------------------------------

interface NumericInputProps {
  value: number;
  min: number;
  onChange: (v: number) => void;
  disabled?: boolean;
  'aria-label'?: string;
  flex1?: boolean;
  suffix?: string;
  integer?: boolean;
}

function NumericInput({
  value,
  min,
  onChange,
  disabled,
  'aria-label': ariaLabel,
  flex1,
  suffix,
  integer = false,
}: NumericInputProps) {
  const fmt = (v: number) =>
    integer ? String(Math.round(v)) : Number.isInteger(v) ? String(v) : v.toFixed(1);

  const [raw, setRaw] = useState(() => fmt(value));
  const [prevValue, setPrevValue] = useState(value);
  if (prevValue !== value) {
    setPrevValue(value);
    setRaw(fmt(value));
  }

  function commit() {
    const parsed = parseFloat(raw);
    const valid = Number.isFinite(parsed) && parsed >= min;
    const committed = valid ? (integer ? Math.round(parsed) : parsed) : value;
    setRaw(fmt(committed));
    if (valid) onChange(committed);
  }

  return (
    <div
      role="group"
      aria-label={ariaLabel}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        background: 'rgba(255,255,255,0.05)',
        borderRadius: '10px',
        padding: '4px 10px',
        ...(flex1 ? { flex: 1 } : {}),
      }}
    >
      <input
        type="text"
        inputMode={integer ? 'numeric' : 'decimal'}
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') (e.target as HTMLInputElement).blur();
        }}
        disabled={disabled}
        style={{
          background: 'transparent',
          border: 'none',
          outline: 'none',
          color: disabled ? 'var(--text-muted)' : 'var(--text)',
          fontSize: flex1 ? '14px' : '15px',
          fontWeight: 700,
          textAlign: 'center',
          width: flex1 ? '100%' : '34px',
          minWidth: 0,
          fontVariantNumeric: 'tabular-nums',
          cursor: disabled ? 'not-allowed' : 'text',
        }}
      />
      {suffix && (
        <span
          style={{
            fontSize: '13px',
            color: 'var(--text-muted)',
            fontWeight: 600,
            flexShrink: 0,
          }}
        >
          {suffix}
        </span>
      )}
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

  // Suggestions can arrive after the row is shown (they load separately).
  // Apply them while the set is neither logged nor edited by hand.
  const [seed, setSeed] = useState({ reps: suggestedReps, weight: suggestedWeight });
  const [edited, setEdited] = useState(false);
  if (!edited && !log && (seed.reps !== suggestedReps || seed.weight !== suggestedWeight)) {
    setSeed({ reps: suggestedReps, weight: suggestedWeight });
    setReps(suggestedReps);
    setWeight(suggestedWeight ?? 0);
  }

  const logSet = useLogSet();
  const updateLog = useUpdateLog();
  const deleteLog = useDeleteExerciseLog();

  const isLogged = !!log;
  const isPending = logSet.isPending || updateLog.isPending || deleteLog.isPending;
  const isDisabled = sessionCompleted || isPending;

  // Read-only summary once the session is completed.
  if (sessionCompleted && log) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 10px',
          borderRadius: '14px',
          background: 'rgba(43,229,129,0.08)',
          border: '1px solid rgba(43,229,129,0.2)',
        }}
      >
        <span
          style={{
            fontSize: '12px',
            fontWeight: 700,
            color: 'var(--text-muted)',
            width: '52px',
            flexShrink: 0,
          }}
        >
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
        : Number.isFinite(weight) && weight >= 0
          ? weight
          : 0;

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
    setEdited(true);
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

  function handleWeightChange(newWeight: number) {
    setWeight(newWeight);
    setEdited(true);
    // If already logged, PATCH immediately
    if (isLogged && log) {
      const weightKg = Number.isFinite(newWeight) && newWeight >= 0 ? newWeight : 0;
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

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 10px',
        borderRadius: '14px',
        background: 'rgba(255,255,255,0.03)',
        border: '1px solid rgba(255,255,255,0.06)',
        transition: 'opacity 0.2s',
        opacity: isLogged ? 0.75 : 1,
      }}
    >
      <span
        style={{
          fontSize: '12px',
          fontWeight: 700,
          color: 'var(--text-muted)',
          width: '52px',
          flexShrink: 0,
        }}
      >
        Serie {setNumber}
      </span>

      {/* Reps input */}
      <NumericInput
        value={reps}
        min={1}
        onChange={handleRepsChange}
        disabled={isDisabled}
        aria-label={`Repeticiones, serie ${setNumber}`}
        integer
      />

      {/* Weight input — expands to fill remaining space */}
      {!isBodyweight && (
        <NumericInput
          value={weight}
          min={0}
          onChange={handleWeightChange}
          disabled={isDisabled}
          aria-label={`Peso kg, serie ${setNumber}`}
          flex1
          suffix="kg"
        />
      )}
      {isBodyweight && (
        <span className="text-xs text-muted px-2 flex-1">Peso corporal</span>
      )}

      {/* Done toggle */}
      <button
        type="button"
        onClick={handleToggleDone}
        disabled={isDisabled}
        aria-label={isLogged ? `Desmarcar serie ${setNumber}` : `Marcar serie ${setNumber} como hecha`}
        aria-pressed={isLogged}
        style={{
          width: '36px',
          height: '36px',
          flexShrink: 0,
          borderRadius: '11px',
          background: isLogged ? 'var(--neon-green)' : 'transparent',
          border: isLogged
            ? '1.5px solid var(--neon-green)'
            : '1.5px solid rgba(43,229,129,0.4)',
          color: isLogged ? 'var(--bg)' : 'var(--neon-green)',
          cursor: isDisabled ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity: isDisabled ? 0.4 : 1,
          transition: 'background 0.15s, color 0.15s',
        }}
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
  // Latest logged set per set number of the exercise done in this slot.
  lastSets: Map<number, LastSetResponse>;
  workoutId: string;
  dayId: string;
  sessionCompleted: boolean;
  onDoneSetsChange: (delta: number) => void;
  extraSets: number;
  onAddExtraSet: () => void;
  // Planned exercise's name when this session does another one instead.
  swappedFrom: string | null;
  canSwap: boolean;
  onSwap: () => void;
  onUndoSwap: () => void;
  // First exercise of the day: the main lift, highlighted.
  isMain: boolean;
  // The other machine type of this exercise ("discos" / "placas"), if any.
  twinLabel: string | null;
  onSwapToTwin: () => void;
  errorMessage: string | null;
}

const swapButtonStyle = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '4px',
  height: '28px',
  padding: '0 10px',
  borderRadius: '10px',
  background: '#0f130f',
  border: '1px solid rgba(255,255,255,0.08)',
  color: 'var(--text-muted)',
  fontSize: '12px',
  fontWeight: 600,
  cursor: 'pointer',
} as const;

function ExerciseBlock({
  sessionId,
  exercise,
  exerciseName,
  muscleGroup,
  isBodyweight,
  logs,
  lastSets,
  workoutId,
  dayId,
  sessionCompleted,
  onDoneSetsChange,
  extraSets,
  onAddExtraSet,
  swappedFrom,
  canSwap,
  onSwap,
  onUndoSwap,
  isMain,
  twinLabel,
  onSwapToTwin,
  errorMessage,
}: ExerciseBlockProps) {
  const logsBySet = new Map(logs.map((l) => [l.set_number, l]));
  const totalSets = exercise.sets + extraSets;
  // The plan's weight belongs to the planned exercise, not to a substitute.
  const planWeight = swappedFrom ? null : exercise.weight_kg;

  return (
    <section
      aria-label={`Ejercicio ${exerciseName}`}
      style={{
        borderRadius: '20px',
        padding: '18px',
        background: '#111511',
        border: isMain ? '1px solid rgba(43,229,129,0.45)' : '1px solid rgba(255,255,255,0.07)',
      }}
    >
      <div className="mb-3" style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          {isMain && (
            <div style={{ marginBottom: '6px' }}>
              <MainExerciseBadge />
            </div>
          )}
          <h3 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text)', fontFamily: "'Barlow Semi Condensed', sans-serif", margin: 0 }}>{exerciseName}</h3>
          {swappedFrom && (
            <p style={{ fontSize: '12px', color: 'var(--neon-green)', fontWeight: 600, marginTop: '2px' }}>
              <span>En lugar de {swappedFrom}</span>
              {canSwap && (
                <>
                  {' · '}
                  <button
                    type="button"
                    onClick={onUndoSwap}
                    aria-label={`Deshacer cambio de ${exerciseName}`}
                    style={{ background: 'none', border: 'none', padding: 0, color: 'var(--text-muted)', fontSize: '12px', fontWeight: 600, textDecoration: 'underline', cursor: 'pointer' }}
                  >
                    Deshacer
                  </button>
                </>
              )}
            </p>
          )}
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginTop: '4px' }}>
            {muscleGroup && `${muscleGroup} · `}
            {exercise.sets} series · {exercise.reps_per_set} reps
          </p>
          {errorMessage && <p className="text-xs text-danger" style={{ marginTop: '4px' }}>{errorMessage}</p>}
        </div>
        {canSwap && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px', flexShrink: 0 }}>
            <button
              type="button"
              onClick={onSwap}
              aria-label={`Cambiar ejercicio ${exerciseName}`}
              style={swapButtonStyle}
            >
              <ArrowLeftRight size={14} />
              Cambiar
            </button>
            {twinLabel && (
              <button type="button" onClick={onSwapToTwin} style={swapButtonStyle}>
                Cambiar a {twinLabel}
              </button>
            )}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {Array.from({ length: totalSets }, (_, i) => i + 1).map((setNum) => {
          const lastLog = lastSets.get(setNum);
          return (
            <SetRow
              key={setNum}
              sessionId={sessionId}
              exercise={exercise}
              setNumber={setNum}
              suggestedReps={lastLog?.reps_completed ?? exercise.reps_per_set}
              suggestedWeight={lastLog?.weight_kg ?? planWeight}
              isBodyweight={isBodyweight}
              existingLog={logsBySet.get(setNum)}
              workoutId={workoutId}
              dayId={dayId}
              sessionCompleted={sessionCompleted}
              onDoneSetsChange={onDoneSetsChange}
            />
          );
        })}
      </div>
      {!sessionCompleted && (
        <button
          type="button"
          onClick={onAddExtraSet}
          className="mt-3 text-xs text-muted bg-transparent border-none cursor-pointer p-0"
        >
          + Serie extra
        </button>
      )}
    </section>
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
  const deleteSession = useDeleteSession();
  const swapExercise = useSwapExercise();
  const undoSwap = useUndoExerciseSwap();
  // Planned slot whose replacement is being picked.
  const [swapSlot, setSwapSlot] = useState<WorkoutExerciseResponse | null>(null);

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

  // When the user picks "Nueva sesión", the old in-progress session is deleted
  // BEFORE the new one is created (non-atomic). If the delete succeeds but the
  // POST fails, the old session is already gone — so we remember that we already
  // abandoned it and offer a retry that only re-runs the start (no re-delete).
  const [abandonedSessionId, setAbandonedSessionId] = useState<string | null>(null);

  // Inline confirmation state — replaces window.confirm for "Nueva sesión".
  // Stores the session ID to abandon so the confirm/cancel handlers can close it.
  const [confirmAbandonId, setConfirmAbandonId] = useState<string | null>(null);

  const session = newSession;

  // Persist the active session ID across refreshes so the "Retomar / Nueva
  // sesión" prompt is skipped when returning to a session the user just started
  // or explicitly resumed this visit.
  const activeSessionKey = `gymjam:active-session:${workoutId}:${dayId}`;

  // Auto-resume guard — tracks which session ID we already triggered auto-resume
  // for, so the "adjust during render" setState below doesn't loop.
  const [autoResumedId, setAutoResumedId] = useState<string | null>(null);
  if (!newSession && !sessionsLoading && inProgressFromHistory) {
    const stored = sessionStorage.getItem(activeSessionKey);
    if (stored === inProgressFromHistory.id && autoResumedId !== inProgressFromHistory.id) {
      setAutoResumedId(inProgressFromHistory.id);
      setNewSession({
        id: inProgressFromHistory.id,
        status: inProgressFromHistory.status,
        logs: inProgressFromHistory.logs,
        started_at: inProgressFromHistory.started_at,
      });
    }
  }

  // The server completes a session after an hour without activity. Drop the
  // local copy so the page offers a new session instead of logging into a
  // finished one.
  const serverCopy = pastSessions?.find((s) => s.id === newSession?.id);
  if (newSession?.status === 'in_progress' && serverCopy?.status === 'completed') {
    setNewSession(null);
  }

  // Set suggestions: the latest logged sets of each exercise done this
  // session, in any routine or day. A swap asks for the new exercise's sets.
  const plannedExercises = workout?.training_days.find((d) => d.id === dayId)?.exercises ?? [];
  const { data: lastSets } = useLastSets(
    newSession ? plannedExercises.map((ex) => doneExerciseId(serverCopy?.swaps, ex)) : [],
  );
  const lastSetsByExercise = new Map<string, Map<number, LastSetResponse>>();
  for (const set of lastSets ?? []) {
    const bySet = lastSetsByExercise.get(set.exercise_id) ?? new Map<number, LastSetResponse>();
    bySet.set(set.set_number, set);
    lastSetsByExercise.set(set.exercise_id, bySet);
  }

  // Live timer — wall-clock time since the server's started_at, so it keeps
  // counting while the screen is locked, survives the tab being discarded and
  // matches the duration saved in the history. Browsers freeze intervals in
  // the background, so returning to the page re-reads the clock at once.
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!session) return;
    const tick = () => setNow(Date.now());
    const intervalId = setInterval(tick, 1000);
    document.addEventListener('visibilitychange', tick);
    return () => {
      clearInterval(intervalId);
      document.removeEventListener('visibilitychange', tick);
    };
  }, [session?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const elapsedSeconds = session
    ? Math.max(0, Math.floor((now - new Date(session.started_at).getTime()) / 1000))
    : 0;

  // Done-sets counter — seeded from the session's existing logs so it is
  // correct immediately when resuming a session, then updated via callbacks
  // from SetRow as the user toggles sets during the current session.
  // Adjusted during render (React-recommended pattern) to avoid cascading
  // setState-in-effect cycles.
  const [prevSessionId, setPrevSessionId] = useState<string | undefined>(session?.id);
  const [doneSets, setDoneSets] = useState(session?.logs.length ?? 0);

  if (session?.id !== prevSessionId) {
    setPrevSessionId(session?.id);
    setDoneSets(session?.logs.length ?? 0);
  }

  const handleDoneSetsChange = useCallback((delta: number) => {
    setDoneSets((prev) => Math.max(0, prev + delta));
  }, []);

  const [extraSetsMap, setExtraSetsMap] = useState<Record<string, number>>({});
  const handleAddExtraSet = useCallback((exerciseId: string) => {
    setExtraSetsMap((prev) => ({ ...prev, [exerciseId]: (prev[exerciseId] ?? 0) + 1 }));
  }, []);

  // ---------------------------------------------------------------------------
  // Rest timer state
  // ---------------------------------------------------------------------------
  const [timerOpen, setTimerOpen] = useState(false);
  const [tMode, setTMode] = useState<'rest' | 'up'>('rest');
  const [tRunning, setTRunning] = useState(false);
  const [tDone, setTDone] = useState(false);
  const [tElapsed, setTElapsed] = useState(0);
  const [tLeft, setTLeft] = useState(90);
  const [tPreset, setTPreset] = useState(90);
  // Wall-clock anchor of the running timer: when the countdown ends (rest) or
  // when the count would have started from zero (up). Each tick re-reads the
  // clock instead of counting ticks, because browsers freeze intervals while
  // the screen is locked.
  const tAnchorRef = useRef(0);
  // Interval effect — starts/stops when tRunning or tMode changes.
  useEffect(() => {
    if (!tRunning) return;
    function tick() {
      if (tMode === 'rest') {
        setTLeft(Math.max(0, Math.ceil((tAnchorRef.current - Date.now()) / 1000)));
      } else {
        setTElapsed(Math.floor((Date.now() - tAnchorRef.current) / 1000));
      }
    }
    const iv = setInterval(tick, 1000);
    document.addEventListener('visibilitychange', tick);
    return () => {
      clearInterval(iv);
      document.removeEventListener('visibilitychange', tick);
    };
  }, [tRunning, tMode]);
  // Completion side-effect — fires when countdown hits zero.
  // setState calls are wrapped in queueMicrotask so they are NOT synchronous
  // in the effect body (avoids cascading-render lint violation while keeping
  // the logic here where tLeft/tDone/tMode are already in the dep array).
  useEffect(() => {
    if (tLeft === 0 && !tDone && tMode === 'rest') {
      queueMicrotask(() => {
        setTRunning(false);
        setTDone(true);
        if (navigator.vibrate) navigator.vibrate(400);
      });
    }
  }, [tLeft, tDone, tMode]);

  // Screen Wake Lock — keep the screen on while the timer is running.
  // The lock is automatically released by the browser when the tab goes to
  // the background; the visibilitychange listener re-acquires it when the
  // user returns. Fails silently on browsers that don't support the API.
  useEffect(() => {
    if (!tRunning || !timerOpen) return;
    if (!('wakeLock' in navigator)) return;

    let lock: WakeLockSentinel | null = null;

    async function acquire() {
      try {
        lock = await navigator.wakeLock.request('screen');
      } catch {
        // Permission denied or feature unavailable — no action needed.
      }
    }

    function handleVisibilityChange() {
      if (document.visibilityState === 'visible') acquire();
    }

    acquire();
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      lock?.release();
    };
  }, [tRunning, timerOpen]);

  function toggleTimer() {
    if (tRunning) {
      setTRunning(false);
    } else if (tDone) {
      setTDone(false);
      setTElapsed(0);
      setTLeft(tPreset);
      startTimer(tPreset, 0);
    } else {
      startTimer(tLeft, tElapsed);
    }
  }

  // Runs the timer on from the given remaining (rest) or elapsed (up) seconds.
  function startTimer(left: number, elapsed: number) {
    tAnchorRef.current = tMode === 'rest' ? Date.now() + left * 1000 : Date.now() - elapsed * 1000;
    setTRunning(true);
  }

  function resetTimer() {
    setTRunning(false);
    setTDone(false);
    setTElapsed(0);
    setTLeft(tPreset);
  }

  function setTimerMode(mode: 'rest' | 'up') {
    setTRunning(false);
    setTDone(false);
    setTElapsed(0);
    setTLeft(tPreset);
    setTMode(mode);
  }

  function setPreset(secs: number) {
    setTRunning(false);
    setTDone(false);
    setTPreset(secs);
    setTLeft(secs);
    setTMode('rest');
  }

  function fmtTimer(s: number) {
    const m = Math.floor(s / 60);
    const r = s % 60;
    return `${m}:${String(r).padStart(2, '0')}`;
  }

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

  // ---------------------------------------------------------------------------
  // Rest timer derived values
  // ---------------------------------------------------------------------------
  const timeLabel = tMode === 'rest' ? fmtTimer(tLeft) : fmtTimer(tElapsed);
  const timeCol = tDone ? '#C6F24E' : '#EAF0EA';
  const playLabel = tRunning ? 'Pausar' : (tDone ? 'Reiniciar' : 'Iniciar');
  const playIcon = tRunning
    ? 'M6 4h4v16H6zM14 4h4v16h-4z'
    : 'M8 5v14l11-7z';
  const statusText = tDone ? '¡Descanso completo!' : (tRunning ? 'En marcha' : 'En pausa');
  const statusCol = tDone ? '#C6F24E' : (tRunning ? '#2BE581' : '#7E8A7E');
  const ringPct = tMode === 'rest' && tPreset
    ? `${(2 * Math.PI * 88 * (1 - tLeft / tPreset)).toFixed(1)} 999`
    : '0 999';
  const presets = [60, 90, 120, 180].map((s) => ({
    label: fmtTimer(s),
    pick: () => setPreset(s),
    bg: tPreset === s && tMode === 'rest' ? 'rgba(43,229,129,0.14)' : '#0f130f',
    border: tPreset === s && tMode === 'rest' ? 'rgba(43,229,129,0.5)' : 'rgba(255,255,255,0.08)',
    col: tPreset === s && tMode === 'rest' ? '#2BE581' : '#9fb0a2',
  }));

  function doStart() {
    startSession.mutate(
      { workoutId, dayId },
      {
        onSuccess: (data) => {
          sessionStorage.setItem(activeSessionKey, data.id);
          setNewSession({
            id: data.id,
            status: data.status,
            logs: data.logs,
            started_at: data.started_at,
          });
          // Start succeeded — clear any abandoned-retry state.
          setAbandonedSessionId(null);
        },
      },
    );
  }

  function handleStart(abandonSessionId?: string) {
    if (abandonSessionId) {
      // Show the inline confirmation dialog instead of window.confirm.
      setConfirmAbandonId(abandonSessionId);
    } else {
      doStart();
    }
  }

  function handleConfirmAbandon() {
    const abandonSessionId = confirmAbandonId;
    if (!abandonSessionId) return;
    setConfirmAbandonId(null);
    deleteSession.mutate(
      { sessionId: abandonSessionId, workoutId, dayId },
      {
        onSuccess: () => {
          // The old session is now gone. Record that so a failed start can be
          // retried without deleting again, then start the new session.
          setAbandonedSessionId(abandonSessionId);
          doStart();
        },
      },
    );
  }

  function handleCancelAbandon() {
    setConfirmAbandonId(null);
  }

  function handleComplete() {
    if (!session) return;
    completeSession.mutate(
      { sessionId: session.id, workoutId, dayId },
      {
        onSuccess: () => {
          sessionStorage.removeItem(activeSessionKey);
          navigate(`/workouts/${workoutId}`);
        },
      },
    );
  }

  const sortedExercises = [...day.exercises].sort((a, b) => a.order - b.order);

  // Swaps and logged slots come from the server copy of the active session:
  // the local `session` snapshot is not refreshed after each mutation.
  const liveSession = (pastSessions ?? []).find((s) => s.id === session?.id);
  const loggedSlots = new Set((liveSession?.logs ?? []).map((l) => l.workout_exercise_id));
  function handleSwapSelect(exerciseId: string) {
    if (!session || !swapSlot) return;
    swapExercise.mutate(
      { sessionId: session.id, workoutExerciseId: swapSlot.id, exerciseId, workoutId, dayId },
      { onSuccess: () => setSwapSlot(null) },
    );
  }

  const swapErrorMessage = !swapExercise.isError
    ? null
    : swapExercise.error instanceof ApiError && swapExercise.error.status === 409
      ? 'Ya hay series registradas en este ejercicio. Bórralas para poder cambiarlo.'
      : 'No se pudo cambiar el ejercicio. Inténtalo de nuevo.';

  // Progress bar stats — includes extra sets added during this session
  const totalSets = sortedExercises.reduce((sum, ex) => sum + ex.sets + (extraSetsMap[ex.id] ?? 0), 0);
  const progressPct = totalSets > 0 ? Math.min(100, (doneSets / totalSets) * 100) : 0;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
        <button
          type="button"
          onClick={() => navigate(`/workouts/${workoutId}`)}
          aria-label="Volver"
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '12px',
            background: '#151A15',
            border: '1px solid rgba(255,255,255,0.08)',
            color: '#EAF0EA',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '21px', fontWeight: 700, color: '#EAF0EA', fontFamily: "'Barlow Semi Condensed', sans-serif" }}>
            {workout.name}
          </div>
          <div style={{ fontSize: '13px', color: '#7E8A7E', fontWeight: 500 }}>
            {dayLabel}{session ? ' · en curso' : ''}
          </div>
        </div>
        {session && (
          <div aria-label="Tiempo transcurrido" style={{ flexShrink: 0 }}>
            <span style={{ fontFamily: "'Barlow Semi Condensed', sans-serif", fontWeight: 700, fontSize: '20px', color: '#2BE581', fontVariantNumeric: 'tabular-nums' }}>
              {formatElapsed(elapsedSeconds)}
            </span>
          </div>
        )}
      </div>

      {/* Progress bar — only while session is active */}
      {session && (
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Progreso</span>
            <span style={{ color: '#2BE581' }}>{doneSets}/{totalSets} series</span>
          </div>
          <div
            style={{ height: '8px', borderRadius: '4px', background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}
            role="progressbar"
            aria-valuenow={doneSets}
            aria-valuemin={0}
            aria-valuemax={totalSets}
          >
            <div
              style={{
                height: '100%',
                borderRadius: '4px',
                background: 'linear-gradient(90deg,#2BE581,#C6F24E)',
                transition: 'width 0.3s',
                width: `${progressPct}%`,
              }}
            />
          </div>
        </div>
      )}

      {/* Loading existing sessions */}
      {!session && sessionsLoading && <Spinner />}

      {/* Resume confirmation */}
      {!newSession && inProgressFromHistory && !sessionsLoading && !(abandonedSessionId !== null && (startSession.isError || startSession.isPending)) && (
        <div
          className="rounded-card border border-border bg-surface p-4 mb-4"
          role="alert"
        >
          {confirmAbandonId ? (
            /* Inline confirmation — replaces window.confirm */
            <>
              <p className="text-sm font-semibold text-text mb-1">
                ¿Eliminar sesión en progreso?
              </p>
              <p className="text-xs text-muted mb-3">
                Se eliminará la sesión en progreso y se iniciará una nueva. Esta acción no se puede deshacer.
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleConfirmAbandon}
                  disabled={deleteSession.isPending}
                  className="text-sm font-semibold rounded-btn bg-danger text-white border-none cursor-pointer px-4 h-9 disabled:opacity-60"
                >
                  {deleteSession.isPending ? 'Eliminando…' : 'Sí, eliminar'}
                </button>
                <button
                  type="button"
                  onClick={handleCancelAbandon}
                  disabled={deleteSession.isPending}
                  className="text-sm font-semibold rounded-btn bg-transparent border border-border text-text cursor-pointer px-4 h-9 disabled:opacity-60"
                >
                  Cancelar
                </button>
              </div>
            </>
          ) : (
            /* Normal resume / new session options */
            <>
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
                  onClick={() => {
                    sessionStorage.setItem(activeSessionKey, inProgressFromHistory.id);
                    setNewSession({
                      id: inProgressFromHistory.id,
                      status: inProgressFromHistory.status,
                      logs: inProgressFromHistory.logs,
                      started_at: inProgressFromHistory.started_at,
                    });
                  }}
                  className="text-sm font-semibold rounded-btn bg-accent text-bg border-none cursor-pointer px-4 h-9"
                >
                  Retomar
                </button>
                <button
                  type="button"
                  onClick={() => handleStart(inProgressFromHistory.id)}
                  disabled={startSession.isPending || deleteSession.isPending}
                  className="text-sm font-semibold rounded-btn bg-transparent border border-border text-text cursor-pointer px-4 h-9 disabled:opacity-60"
                >
                  {startSession.isPending || deleteSession.isPending ? 'Iniciando…' : 'Nueva sesión'}
                </button>
              </div>
            </>
          )}
          {deleteSession.isError && (
            <p className="mt-2 text-xs text-danger">
              No se pudo eliminar la sesión anterior:{' '}
              {(deleteSession.error as Error).message}
            </p>
          )}
          {/* Start error while the in-progress session still exists (delete
              hasn't run or failed) — the abandoned-retry recovery block below
              handles the delete-succeeded-but-start-failed case. */}
          {abandonedSessionId === null && startSession.isError && (
            <p className="mt-2 text-xs text-danger">
              {(startSession.error as Error).message}
            </p>
          )}
        </div>
      )}

      {/* Abandoned-session recovery — rendered independently of
          inProgressFromHistory. When "Nueva sesión" deletes the old session but
          the subsequent start fails, the old session is already gone, so
          inProgressFromHistory becomes null and its block unmounts. This block
          survives that transition and lets the user retry the start (no
          re-delete). */}
      {abandonedSessionId !== null && (startSession.isError || startSession.isPending) && !newSession && (
        <div
          className="rounded-card border border-border bg-surface p-4 mb-4"
          role="alert"
        >
          {startSession.isError && (
            <p className="text-xs text-danger mb-2">
              Se eliminó la sesión anterior pero no se pudo iniciar la nueva:{' '}
              {(startSession.error as Error).message}
            </p>
          )}
          <button
            type="button"
            onClick={() => doStart()}
            disabled={startSession.isPending}
            className="text-sm font-semibold rounded-btn bg-accent text-bg border-none cursor-pointer px-4 h-9 disabled:opacity-60"
          >
            {startSession.isPending ? 'Iniciando…' : 'Intentar de nuevo'}
          </button>
        </div>
      )}

      {/* Pre-start state */}
      {!newSession && !sessionsLoading && !inProgressFromHistory && (abandonedSessionId === null || (!startSession.isError && !startSession.isPending)) && (
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
                onClick={() => handleStart()}
                disabled={startSession.isPending}
                style={{
                  width: '100%',
                  height: '54px',
                  border: 'none',
                  borderRadius: '16px',
                  background: 'linear-gradient(135deg,#2BE581,#1fbd6a)',
                  color: 'rgb(6,33,15)',
                  fontSize: '16px',
                  fontWeight: 700,
                  cursor: startSession.isPending ? 'not-allowed' : 'pointer',
                  opacity: startSession.isPending ? 0.6 : 1,
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
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
            {sortedExercises.map((exercise, index) => {
              const exerciseLogs = session.logs.filter(
                (l) => l.workout_exercise_id === exercise.id,
              );
              const doneId = doneExerciseId(liveSession?.swaps, exercise);
              const catalogExercise = exerciseById.get(doneId);
              const plannedExercise = exerciseById.get(exercise.exercise_id);
              const isSwapped = doneId !== exercise.exercise_id;
              const twin = machineTwin(doneId);
              const twinInCatalog = twin !== null && exerciseById.has(twin.id);
              return (
                <ExerciseBlock
                  // Remount on swap so set rows re-seed their suggestions.
                  key={`${exercise.id}:${doneId}`}
                  sessionId={session.id}
                  exercise={exercise}
                  exerciseName={catalogExercise?.name ?? doneId}
                  muscleGroup={catalogExercise?.muscle_group ?? ''}
                  isBodyweight={catalogExercise?.is_bodyweight ?? false}
                  logs={exerciseLogs}
                  lastSets={lastSetsByExercise.get(doneId) ?? new Map()}
                  swappedFrom={isSwapped ? (plannedExercise?.name ?? exercise.exercise_id) : null}
                  canSwap={session.status === 'in_progress' && !loggedSlots.has(exercise.id)}
                  onSwap={() => {
                    swapExercise.reset();
                    setSwapSlot(exercise);
                  }}
                  onUndoSwap={() =>
                    undoSwap.mutate({ sessionId: session.id, workoutExerciseId: exercise.id, workoutId, dayId })
                  }
                  isMain={index === 0}
                  twinLabel={twinInCatalog ? twin.label : null}
                  onSwapToTwin={() => {
                    if (!twin) return;
                    swapExercise.reset();
                    swapExercise.mutate({
                      sessionId: session.id,
                      workoutExerciseId: exercise.id,
                      exerciseId: twin.id,
                      workoutId,
                      dayId,
                    });
                  }}
                  errorMessage={
                    undoSwap.isError && undoSwap.variables?.workoutExerciseId === exercise.id
                      ? 'No se pudo deshacer el cambio. Inténtalo de nuevo.'
                      : !swapSlot && swapExercise.isError && swapExercise.variables?.workoutExerciseId === exercise.id
                        ? swapErrorMessage
                        : null
                  }
                  workoutId={workoutId}
                  dayId={dayId}
                  sessionCompleted={session.status === 'completed'}
                  onDoneSetsChange={handleDoneSetsChange}
                  extraSets={extraSetsMap[exercise.id] ?? 0}
                  onAddExtraSet={() => handleAddExtraSet(exercise.id)}
                />
              );
            })}
          </div>

          {session.status === 'in_progress' && (
            <button
              type="button"
              onClick={handleComplete}
              disabled={completeSession.isPending}
              style={{
                width: '100%',
                height: '54px',
                marginTop: '18px',
                border: 'none',
                borderRadius: '16px',
                background: 'linear-gradient(135deg,#2BE581,#1fbd6a)',
                color: 'rgb(6,33,15)',
                fontSize: '16px',
                fontWeight: 700,
                fontFamily: 'Barlow, sans-serif',
                cursor: completeSession.isPending ? 'not-allowed' : 'pointer',
                boxShadow: '0 8px 24px rgba(43,229,129,0.3)',
                opacity: completeSession.isPending ? 0.6 : 1,
              }}
            >
              {completeSession.isPending ? 'Completando…' : 'Completar sesión'}
            </button>
          )}
          {completeSession.isError && (
            <p className="mt-3 text-xs text-danger text-right">
              {(completeSession.error as Error).message}
            </p>
          )}

          {swapSlot && (
            <ExerciseSwapSheet
              current={exerciseById.get(doneExerciseId(liveSession?.swaps, swapSlot))}
              currentName={
                exerciseById.get(doneExerciseId(liveSession?.swaps, swapSlot))?.name ??
                doneExerciseId(liveSession?.swaps, swapSlot)
              }
              catalog={exercises ?? []}
              isPending={swapExercise.isPending}
              errorMessage={swapErrorMessage}
              onSelect={handleSwapSelect}
              onClose={() => {
                // A failed swap's error belongs to the sheet; don't let it
                // resurface under the exercise once the sheet is closed.
                swapExercise.reset();
                setSwapSlot(null);
              }}
            />
          )}
        </>
      )}

      {/* Timer button — fixed inside the AppHeader zone, stays visible while scrolling */}
      {session && !timerOpen && (
        <button
          type="button"
          onClick={() => setTimerOpen(true)}
          className="fixed right-4 md:right-8 z-30"
          style={{
            top: 'calc(env(safe-area-inset-top) + 6px)',
            width: 44, height: 44, borderRadius: 14,
            background: tRunning ? 'rgba(43,229,129,0.18)' : 'rgba(43,229,129,0.10)',
            border: `1px solid ${tRunning ? 'rgba(43,229,129,0.6)' : 'rgba(43,229,129,0.3)'}`,
            color: '#2BE581', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
          aria-label="Abrir cronómetro"
        >
          {tRunning && (
            <span
              className="absolute animate-ping"
              style={{ width: 44, height: 44, borderRadius: 14, background: 'rgba(43,229,129,0.2)', inset: 0 }}
            />
          )}
          <svg width="21" height="21" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2"
            strokeLinecap="round" strokeLinejoin="round"
            style={{ position: 'relative' }}
          >
            <circle cx="12" cy="13" r="8"/>
            <path d="M12 9.5V13l2.5 1.5M9 2h6M18.5 6.5l1.5-1.5"/>
          </svg>
        </button>
      )}

      {/* Rest timer bottom sheet */}
      {timerOpen && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 60 }}>
          {/* Scrim */}
          <div
            onClick={() => setTimerOpen(false)}
            style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(4px)' }}
          />
          {/* Panel */}
          <div
            role="dialog"
            aria-modal={true}
            aria-labelledby="timer-dialog-heading"
            tabIndex={-1}
            onKeyDown={(e) => { if (e.key === 'Escape') setTimerOpen(false); }}
            style={{
              position: 'absolute', bottom: 0, left: 0, right: 0,
              background: '#0a0f0a',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '28px 28px 0 0',
              padding: '0 0 40px',
              maxHeight: '92dvh',
              overflowY: 'auto',
            }}
          >
            {/* Drag handle */}
            <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '12px', paddingBottom: '4px' }}>
              <div style={{ width: 40, height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.12)' }} />
            </div>

            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 20px 16px' }}>
              <div>
                <div id="timer-dialog-heading" style={{ fontSize: '18px', fontWeight: 700, color: '#EAF0EA', fontFamily: "'Barlow Semi Condensed', sans-serif" }}>
                  Cronómetro
                </div>
                <div style={{ fontSize: '12px', color: '#7E8A7E', fontWeight: 500, marginTop: '2px' }}>
                  {dayLabel}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setTimerOpen(false)}
                style={{
                  width: 36, height: 36, borderRadius: 10,
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: '#7E8A7E', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}
                aria-label="Cerrar cronómetro"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </button>
            </div>

            {/* Mode selector */}
            <div style={{ display: 'flex', gap: '8px', padding: '0 20px 20px' }}>
              {(['rest', 'up'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setTimerMode(mode)}
                  style={{
                    flex: 1, height: 38, borderRadius: 10,
                    background: tMode === mode ? 'rgba(43,229,129,0.14)' : 'rgba(255,255,255,0.04)',
                    border: tMode === mode ? '1px solid rgba(43,229,129,0.5)' : '1px solid rgba(255,255,255,0.08)',
                    color: tMode === mode ? '#2BE581' : '#7E8A7E',
                    fontSize: '13px', fontWeight: 600, cursor: 'pointer',
                    fontFamily: "'Barlow', sans-serif",
                  }}
                >
                  {mode === 'rest' ? 'Descanso' : 'Ascendente'}
                </button>
              ))}
            </div>

            {/* Ring + digits */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '0 20px 20px' }}>
              <div style={{ position: 'relative', width: 200, height: 200 }}>
                <svg width="200" height="200" viewBox="0 0 200 200" style={{ transform: 'rotate(-90deg)' }}>
                  {/* Track */}
                  <circle cx="100" cy="100" r="88" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10"/>
                  {/* Progress */}
                  <circle
                    cx="100" cy="100" r="88"
                    fill="none"
                    stroke={tDone ? '#C6F24E' : '#2BE581'}
                    strokeWidth="10"
                    strokeLinecap="round"
                    strokeDasharray={ringPct}
                    style={{ transition: 'stroke-dasharray 0.5s linear' }}
                  />
                </svg>
                {/* Centered text */}
                <div style={{
                  position: 'absolute', inset: 0,
                  display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                }}>
                  <span
                    aria-label="Tiempo del cronómetro"
                    style={{
                      fontSize: '48px', fontWeight: 700, color: timeCol,
                      fontFamily: "'Barlow Semi Condensed', sans-serif",
                      fontVariantNumeric: 'tabular-nums',
                      lineHeight: 1,
                    }}
                  >
                    {timeLabel}
                  </span>
                  <span style={{ fontSize: '12px', color: statusCol, fontWeight: 600, marginTop: '6px' }}>
                    {statusText}
                  </span>
                </div>
              </div>
            </div>

            {/* Presets — only in rest mode */}
            {tMode === 'rest' && (
              <div style={{ display: 'flex', gap: '8px', padding: '0 20px 20px' }}>
                {presets.map((p) => (
                  <button
                    key={p.label}
                    type="button"
                    onClick={p.pick}
                    style={{
                      flex: 1, height: 36, borderRadius: 10,
                      background: p.bg,
                      border: `1px solid ${p.border}`,
                      color: p.col,
                      fontSize: '13px', fontWeight: 600, cursor: 'pointer',
                      fontFamily: "'Barlow', sans-serif",
                    }}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            )}

            {/* Controls */}
            <div style={{ display: 'flex', gap: '12px', padding: '0 20px' }}>
              {/* Reset */}
              <button
                type="button"
                onClick={resetTimer}
                style={{
                  width: 52, height: 52, borderRadius: 14, flexShrink: 0,
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: '#9fb0a2', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}
                aria-label="Reiniciar cronómetro"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                  <path d="M3 3v5h5"/>
                </svg>
              </button>

              {/* Play / Pause */}
              <button
                type="button"
                onClick={toggleTimer}
                style={{
                  flex: 1, height: 52, borderRadius: 14,
                  background: tDone ? 'rgba(198,242,78,0.15)' : 'rgba(43,229,129,0.15)',
                  border: tDone ? '1px solid rgba(198,242,78,0.4)' : '1px solid rgba(43,229,129,0.4)',
                  color: tDone ? '#C6F24E' : '#2BE581',
                  fontSize: '15px', fontWeight: 700, cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                  fontFamily: "'Barlow', sans-serif",
                }}
                aria-label={playLabel}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d={playIcon}/>
                </svg>
                {playLabel}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
