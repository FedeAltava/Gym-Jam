import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle2 } from 'lucide-react';
import { useWorkout } from '../hooks/useWorkouts';
import { useExercises } from '../hooks/useExercises';
import {
  useStartSession,
  useLogSet,
  useUpdateLog,
  useCompleteSession,
  useSessionsForDay,
  useDeleteExerciseLog,
  useDeleteSession,
} from '../hooks/useSessions';
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
        onFocus={(e) => e.target.select()}
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
  lastSessionLogs: Map<string, ExerciseLogResponse>;
  workoutId: string;
  dayId: string;
  sessionCompleted: boolean;
  onDoneSetsChange: (delta: number) => void;
  extraSets: number;
  onAddExtraSet: () => void;
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
  onDoneSetsChange,
  extraSets,
  onAddExtraSet,
}: ExerciseBlockProps) {
  const logsBySet = new Map(logs.map((l) => [l.set_number, l]));
  const totalSets = exercise.sets + extraSets;

  return (
    <div style={{ borderRadius: '20px', padding: '18px', background: '#111511', border: '1px solid rgba(255,255,255,0.07)' }}>
      <div className="mb-3">
        <h3 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text)', fontFamily: "'Barlow Semi Condensed', sans-serif", margin: 0 }}>{exerciseName}</h3>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginTop: '4px' }}>
          {muscleGroup && `${muscleGroup} · `}
          {exercise.sets} series · {exercise.reps_per_set} reps
        </p>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
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
  const deleteSession = useDeleteSession();

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

  // Live timer — elapsed seconds since session.started_at
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!session) return;
    const startTime = new Date(session.started_at).getTime();
    const tick = () => setElapsedSeconds(Math.floor((Date.now() - startTime) / 1000));
    const initId = setTimeout(tick, 0);
    const id = setInterval(tick, 1000);
    return () => { clearTimeout(initId); clearInterval(id); };
  }, [session]);

  // Done-sets counter — seeded synchronously from the session's existing logs
  // so it is correct immediately when resuming a session, then updated via
  // callbacks from SetRow as the user toggles sets during the current session.
  const [doneSets, setDoneSets] = useState(0);

  useEffect(() => {
    if (session) {
      setDoneSets(session.logs.length);
    }
  }, [session?.id]); // eslint-disable-line react-hooks/exhaustive-deps

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
  // Interval effect — starts/stops when tRunning or tMode changes
  useEffect(() => {
    if (!tRunning) return;
    const iv = setInterval(() => {
      if (tMode === 'rest') {
        setTLeft((prev) => {
          if (prev <= 1) {
            return 0;
          }
          return prev - 1;
        });
      } else {
        setTElapsed((prev) => prev + 1);
      }
    }, 1000);
    return () => { clearInterval(iv); };
  }, [tRunning, tMode]);

  // Completion side-effect effect — fires when countdown hits zero
  useEffect(() => {
    if (tLeft === 0 && !tDone && tMode === 'rest') {
      setTRunning(false);
      setTDone(true);
      if (navigator.vibrate) navigator.vibrate(400);
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
      setTRunning(true);
    } else {
      setTRunning(true);
    }
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
          navigate(`/workouts/${workoutId}`);
        },
      },
    );
  }

  const sortedExercises = [...day.exercises].sort((a, b) => a.order - b.order);

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
        {session && (
          <button
            type="button"
            onClick={() => setTimerOpen(true)}
            style={{
              width: 44, height: 44, flexShrink: 0, borderRadius: 14,
              background: 'rgba(43,229,129,0.10)',
              border: '1px solid rgba(43,229,129,0.3)',
              color: '#2BE581', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
            aria-label="Abrir cronómetro"
          >
            <svg width="21" height="21" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="13" r="8"/>
              <path d="M12 9.5V13l2.5 1.5M9 2h6M18.5 6.5l1.5-1.5"/>
            </svg>
          </button>
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
          <p className="text-xs text-danger mb-2">
            Se eliminó la sesión anterior pero no se pudo iniciar la nueva:{' '}
            {(startSession.error as Error).message}
          </p>
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
        </>
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
