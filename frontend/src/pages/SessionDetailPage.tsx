import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, X } from 'lucide-react';
import { useSessionDetail, useSessionHistory } from '../hooks/useSessionHistory';
import { Spinner } from '../components/Spinner';
import { DAY_LABEL } from '../lib/days';
import type { DayKey } from '../lib/days';
import type { SessionHistoryItemResponse, SessionHistoryLogResponse } from '../types/api';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const longDateFormatter = new Intl.DateTimeFormat('es-ES', {
  day: 'numeric',
  month: 'short',
});

function formatLongDate(iso: string): string {
  return longDateFormatter.format(new Date(iso));
}

function toDayLabel(day: string): string {
  return DAY_LABEL[day as DayKey] ?? day;
}

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds < 0) return '—';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}min`;
  if (m > 0) return `${m}min`;
  return `${seconds}s`;
}

function computeVolume(logs: SessionHistoryItemResponse['logs']): number {
  return logs.reduce((sum, l) => sum + (l.reps_completed * (l.weight_kg ?? 0)), 0);
}

/** Group logs by exercise_name, preserving set order. */
function groupByExercise(
  logs: SessionHistoryLogResponse[],
): Array<{ name: string; muscleGroup: string | null; sets: SessionHistoryLogResponse[] }> {
  const map = new Map<string, { muscleGroup: string | null; sets: SessionHistoryLogResponse[] }>();
  for (const log of logs) {
    const existing = map.get(log.exercise_name);
    if (existing) {
      existing.sets.push(log);
    } else {
      map.set(log.exercise_name, { muscleGroup: log.muscle_group, sets: [log] });
    }
  }
  return Array.from(map.entries()).map(([name, { muscleGroup, sets }]) => ({
    name,
    muscleGroup,
    sets: [...sets].sort((a, b) => a.set_number - b.set_number),
  }));
}

// ---------------------------------------------------------------------------
// buildProgress — computes SVG paths and stats for the exercise progress chart
// ---------------------------------------------------------------------------

interface ProgressPoint {
  cx: string;
  cy: string;
  val: string;
  day: string;
  month: string;
}

interface ProgressStat {
  label: string;
  val: string;
  col: string;
  sub: string;
}

interface ProgressData {
  line: string;
  area: string;
  points: ProgressPoint[];
  stats: ProgressStat[];
  sessionCount: number;
}

const _dayFmt = new Intl.DateTimeFormat('es-ES', { day: 'numeric' });
const _monthFmt = new Intl.DateTimeFormat('es-ES', { month: 'short' });

function buildProgress(
  exerciseName: string,
  sessions: SessionHistoryItemResponse[],
): ProgressData | null {
  // Keep only sessions that have weighted logs for this exercise, oldest first
  const relevant = sessions
    .filter((s) => s.logs.some((l) => l.exercise_name === exerciseName && l.weight_kg != null))
    .sort((a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime());

  if (relevant.length === 0) return null;

  const data = relevant.map((s) => {
    const logs = s.logs.filter((l) => l.exercise_name === exerciseName && l.weight_kg != null);
    const maxKg = Math.max(...logs.map((l) => l.weight_kg!));
    return { date: new Date(s.started_at), maxKg };
  });

  const vals = data.map((d) => d.maxKg);
  const maxV = Math.max(...vals);
  const minV = Math.min(...vals);
  const range = maxV - minV || 1;

  const X0 = 34, X1 = 300, Y0 = 22, Y1 = 132;
  const n = data.length;
  const px = (i: number) => (n === 1 ? (X0 + X1) / 2 : X0 + (X1 - X0) * (i / (n - 1)));
  const py = (v: number) => Y1 - (Y1 - Y0) * ((v - minV) / range);

  const pts = data.map((d, i) => ({ x: px(i), y: py(d.maxKg), maxKg: d.maxKg, date: d.date }));

  const line = pts.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
  const area =
    line +
    ` L${pts[pts.length - 1].x.toFixed(1)} ${Y1}` +
    ` L${pts[0].x.toFixed(1)} ${Y1}` +
    ' Z';

  const points: ProgressPoint[] = pts.map((p) => ({
    cx: p.x.toFixed(1),
    cy: p.y.toFixed(1),
    val: `${p.maxKg}kg`,
    day: _dayFmt.format(p.date),
    month: _monthFmt.format(p.date).toUpperCase().replace('.', ''),
  }));

  const first = vals[0];
  const last = vals[vals.length - 1];
  const gain = +(last - first).toFixed(1);
  const pct = first ? Math.round((gain / first) * 100) : 0;

  const stats: ProgressStat[] = [
    { label: 'Primer registro', val: `${first} kg`, col: 'var(--text)', sub: '' },
    { label: 'Máximo actual', val: `${last} kg`, col: 'var(--text)', sub: '' },
    {
      label: 'Progresión',
      val: `${gain >= 0 ? '+' : ''}${gain} kg`,
      col: '#2BE581',
      sub: `${pct >= 0 ? '+' : ''}${pct}%`,
    },
  ];

  return { line, area, points, stats, sessionCount: n };
}

// ---------------------------------------------------------------------------
// StatTile
// ---------------------------------------------------------------------------

interface StatTileProps {
  value: string;
  label: string;
  valueColor?: string;
}

function StatTile({ value, label, valueColor = 'var(--neon-green)' }: StatTileProps) {
  return (
    <div
      style={{
        flex: 1,
        padding: '14px 8px',
        borderRadius: '16px',
        background: '#111511',
        border: '1px solid rgba(255,255,255,0.07)',
        textAlign: 'center',
      }}
    >
      <div
        style={{
          fontSize: '20px',
          fontWeight: 800,
          color: valueColor,
          fontFamily: "'Barlow Semi Condensed', sans-serif",
          lineHeight: 1,
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontSize: '10px',
          color: 'var(--text-muted)',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          marginTop: '4px',
        }}
      >
        {label}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ExerciseProgressSheet
// ---------------------------------------------------------------------------

interface ExerciseProgressSheetProps {
  exerciseName: string;
  sessions: SessionHistoryItemResponse[];
  onClose: () => void;
}

function ExerciseProgressSheet({ exerciseName, sessions, onClose }: ExerciseProgressSheetProps) {
  const progress = buildProgress(exerciseName, sessions);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-end',
      }}
    >
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(2px)',
        }}
      />

      {/* Sheet */}
      <div
        style={{
          position: 'relative',
          background: '#0d100d',
          borderTopLeftRadius: '28px',
          borderTopRightRadius: '28px',
          borderTop: '1px solid rgba(255,255,255,0.1)',
          padding: '14px 20px 40px',
          boxShadow: '0 -20px 60px rgba(0,0,0,0.5)',
          maxHeight: '80vh',
          overflowY: 'auto',
        }}
      >
        {/* Drag handle */}
        <div
          style={{
            width: '40px',
            height: '5px',
            borderRadius: '3px',
            background: 'rgba(255,255,255,0.18)',
            margin: '0 auto 16px',
          }}
        />

        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            marginBottom: '4px',
          }}
        >
          <div>
            <div
              style={{
                fontSize: '12px',
                fontWeight: 700,
                color: '#2BE581',
                textTransform: 'uppercase',
                letterSpacing: '1px',
              }}
            >
              Progreso
            </div>
            <div
              style={{
                fontSize: '23px',
                fontWeight: 700,
                color: 'var(--text)',
                fontFamily: "'Barlow Semi Condensed', sans-serif",
              }}
            >
              {exerciseName}
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Cerrar"
            style={{
              width: '34px',
              height: '34px',
              flexShrink: 0,
              borderRadius: '11px',
              background: '#151A15',
              border: '1px solid rgba(255,255,255,0.08)',
              color: '#9fb0a2',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <X size={16} />
          </button>
        </div>

        {progress ? (
          <>
            <div
              style={{
                fontSize: '13px',
                color: '#7E8A7E',
                fontWeight: 500,
                marginBottom: '16px',
              }}
            >
              Peso máximo por sesión · últimas {progress.sessionCount}
            </div>

            {/* Chart */}
            <div
              style={{
                borderRadius: '20px',
                background: '#111511',
                border: '1px solid rgba(255,255,255,0.07)',
                padding: '16px 8px 10px',
                marginBottom: '14px',
              }}
            >
              <svg
                viewBox="0 0 320 168"
                style={{ width: '100%', height: 'auto', display: 'block' }}
              >
                <defs>
                  <linearGradient id="exerciseProgressArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2BE581" stopOpacity="0.28" />
                    <stop offset="100%" stopColor="#2BE581" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <line x1="34" y1="22" x2="300" y2="22" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                <line x1="34" y1="77" x2="300" y2="77" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                <line x1="34" y1="132" x2="300" y2="132" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
                <path d={progress.area} fill="url(#exerciseProgressArea)" />
                <path
                  d={progress.line}
                  fill="none"
                  stroke="#2BE581"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {progress.points.map((pt, i) => (
                  <g key={i}>
                    <circle
                      cx={pt.cx}
                      cy={pt.cy}
                      r="4.5"
                      fill="#0d100d"
                      stroke="#2BE581"
                      strokeWidth="3"
                    />
                    <text
                      x={pt.cx}
                      y={pt.cy}
                      dy="-11"
                      textAnchor="middle"
                      fill="var(--text)"
                      fontFamily="Barlow"
                      fontSize="12"
                      fontWeight="700"
                    >
                      {pt.val}
                    </text>
                    <text
                      x={pt.cx}
                      y="150"
                      textAnchor="middle"
                      fill="#9fb0a2"
                      fontFamily="Barlow"
                      fontSize="11"
                      fontWeight="700"
                    >
                      {pt.day}
                    </text>
                    <text
                      x={pt.cx}
                      y="161"
                      textAnchor="middle"
                      fill="#7E8A7E"
                      fontFamily="Barlow"
                      fontSize="9"
                      fontWeight="700"
                      letterSpacing="0.5"
                    >
                      {pt.month}
                    </text>
                  </g>
                ))}
              </svg>
            </div>

            {/* Stats */}
            <div style={{ display: 'flex', gap: '10px' }}>
              {progress.stats.map((st) => (
                <div
                  key={st.label}
                  style={{
                    flex: 1,
                    padding: '14px 12px',
                    borderRadius: '16px',
                    background: '#0f130f',
                    border: '1px solid rgba(255,255,255,0.06)',
                    textAlign: 'center',
                  }}
                >
                  <div
                    style={{
                      fontSize: '19px',
                      fontWeight: 800,
                      fontFamily: "'Barlow Semi Condensed', sans-serif",
                      color: st.col,
                    }}
                  >
                    {st.val}
                  </div>
                  {st.sub && (
                    <div
                      style={{
                        fontSize: '12px',
                        fontWeight: 700,
                        color: '#2BE581',
                        marginTop: '1px',
                      }}
                    >
                      {st.sub}
                    </div>
                  )}
                  <div
                    style={{
                      fontSize: '10px',
                      color: '#7E8A7E',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                      marginTop: '4px',
                    }}
                  >
                    {st.label}
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div
            style={{
              textAlign: 'center',
              padding: '32px 0',
              color: '#7E8A7E',
              fontSize: '14px',
              fontWeight: 500,
            }}
          >
            Sin datos de peso registrados
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ExerciseCard
// ---------------------------------------------------------------------------

interface ExerciseCardProps {
  name: string;
  muscleGroup: string | null;
  sets: SessionHistoryLogResponse[];
  /** Max weight (kg) across ALL exercises in the session; -1 when no PRs. */
  sessionMaxWeight: number;
  onOpenProgress: () => void;
}

function ExerciseCard({ name, muscleGroup, sets, sessionMaxWeight, onOpenProgress }: ExerciseCardProps) {
  const maxWeight = sessionMaxWeight;

  return (
    <div
      style={{
        background: '#111511',
        borderRadius: '20px',
        border: '1px solid rgba(255,255,255,0.07)',
        padding: '16px',
      }}
    >
      {/* Header — tap to open progress chart */}
      <button
        onClick={onOpenProgress}
        style={{
          width: '100%',
          textAlign: 'left',
          background: 'none',
          border: 'none',
          padding: 0,
          cursor: 'pointer',
          fontFamily: "'Barlow', sans-serif",
          marginBottom: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '10px',
        }}
      >
        <div style={{ minWidth: 0 }}>
          <div
            style={{
              fontSize: '17px',
              fontWeight: 700,
              color: 'var(--text)',
              fontFamily: "'Barlow Semi Condensed', sans-serif",
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {name}
          </div>
          <div
            style={{
              fontSize: '11px',
              color: 'var(--text-muted)',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginTop: '2px',
            }}
          >
            {muscleGroup ? `${muscleGroup} · ` : ''}
            {sets.length} {sets.length === 1 ? 'serie' : 'series'}
          </div>
        </div>
        <span
          style={{
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            fontSize: '11px',
            fontWeight: 700,
            color: '#2BE581',
            background: 'rgba(43,229,129,0.10)',
            padding: '6px 10px',
            borderRadius: '10px',
            whiteSpace: 'nowrap',
          }}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#2BE581"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 3v18h18" />
            <path d="M7 15l4-4 3 3 5-6" />
          </svg>
          Progreso
        </span>
      </button>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {sets.map((set) => {
          const isPr = sessionMaxWeight > 0 && set.weight_kg != null && set.weight_kg === maxWeight;
          return (
            <div
              key={set.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 12px',
                borderRadius: '12px',
                background: isPr ? 'rgba(198,242,78,0.08)' : 'rgba(255,255,255,0.03)',
                border: `1px solid ${isPr ? 'rgba(198,242,78,0.25)' : 'rgba(255,255,255,0.05)'}`,
              }}
            >
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--text-muted)',
                  width: '52px',
                  flexShrink: 0,
                }}
              >
                Serie {set.set_number}
              </span>
              <span style={{ flex: 1, fontSize: '14px', fontWeight: 700, color: 'var(--text)' }}>
                {set.reps_completed} reps
              </span>
              <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text)' }}>
                {set.weight_kg != null ? `${set.weight_kg} kg` : '—'}
              </span>
              {isPr && (
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 800,
                    color: '#C6F24E',
                    background: 'rgba(198,242,78,0.12)',
                    padding: '3px 8px',
                    borderRadius: '8px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}
                >
                  PR
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SessionDetailPage
// ---------------------------------------------------------------------------

export function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [sheetExercise, setSheetExercise] = useState<string | null>(null);

  const { data: session, isLoading } = useSessionDetail(sessionId);

  // History is used ONLY to find the previous session of the same workout and
  // to provide data for the per-exercise progress chart.
  const { data: historyData } = useSessionHistory({ status: 'completed' });
  const allSessions = historyData?.pages.flatMap((p) => p.items) ?? [];

  if (isLoading && !session) return <Spinner />;

  if (!isLoading && !session) {
    return (
      <div style={{ textAlign: 'center', padding: '48px 0' }}>
        <p style={{ fontSize: '16px', color: 'var(--text-muted)', marginBottom: '20px' }}>
          Sesión no encontrada
        </p>
        <button
          onClick={() => navigate('/history')}
          style={{
            fontSize: '14px',
            fontWeight: 700,
            color: 'var(--neon-green)',
            background: 'transparent',
            border: '1px solid var(--neon-green)',
            borderRadius: '12px',
            padding: '8px 20px',
            cursor: 'pointer',
          }}
        >
          Volver al historial
        </button>
      </div>
    );
  }

  if (!session) return <Spinner />;

  const volume = computeVolume(session.logs);
  const exercises = groupByExercise(session.logs);
  // Session-wide max weight used for PR badge heuristic. -1 when no PRs recorded.
  const sessionMaxWeight =
    session.pr_count > 0
      ? Math.max(...session.logs.map((l) => l.weight_kg ?? 0))
      : -1;
  const dayLabel = toDayLabel(session.day_of_week);
  const dateLabel = formatLongDate(session.started_at);
  const durationLabel = formatDuration(session.duration_seconds);
  const prLabel = `${session.pr_count} ${session.pr_count === 1 ? 'PR' : 'PRs'}`;

  // Previous session of the same workout (most recent before this one)
  const previousSession = allSessions
    .filter(
      (s) =>
        s.workout_id === session.workout_id &&
        s.id !== session.id &&
        new Date(s.started_at) < new Date(session.started_at),
    )
    .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())[0];

  return (
    <>
      <div style={{ paddingBottom: '32px' }}>
        {/* ─── Header ─── */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '20px' }}>
          <button
            onClick={() => navigate(-1)}
            aria-label="Volver"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '38px',
              height: '38px',
              borderRadius: '12px',
              background: '#151A15',
              border: '1px solid rgba(255,255,255,0.08)',
              cursor: 'pointer',
              flexShrink: 0,
              marginTop: '2px',
            }}
          >
            <ArrowLeft size={18} style={{ color: 'var(--text)' }} />
          </button>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              style={{
                fontSize: '22px',
                fontWeight: 700,
                color: 'var(--text)',
                fontFamily: "'Barlow Semi Condensed', sans-serif",
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {session.workout_name}
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 500, marginTop: '3px' }}>
              {dayLabel} · {dateLabel} · completada
            </div>
          </div>
        </div>

        {/* ─── Stats bar ─── */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
          <StatTile
            value={`${Math.round(volume).toLocaleString('es-ES')}`}
            label="Volumen kg"
            valueColor="#2BE581"
          />
          <StatTile value={durationLabel} label="Duración" valueColor="var(--text)" />
          <StatTile value={prLabel} label="Récords" valueColor="#C6F24E" />
        </div>

        {/* ─── Previous session banner ─── */}
        {previousSession && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 14px',
              borderRadius: '14px',
              background: 'rgba(43,229,129,0.06)',
              border: '1px solid rgba(43,229,129,0.15)',
              marginBottom: '16px',
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#2BE581"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M3 3v18h18" />
              <path d="M7 15l4-4 3 3 5-6" />
            </svg>
            <span style={{ fontSize: '13px', color: '#9fb0a2', fontWeight: 500 }}>
              Sesión anterior de {session.workout_name}:{' '}
              <span style={{ color: 'var(--text)', fontWeight: 700 }}>
                {formatLongDate(previousSession.started_at)}
              </span>
            </span>
          </div>
        )}

        {/* ─── Exercise list ─── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
          {exercises.map((ex) => (
            <ExerciseCard
              key={ex.name}
              name={ex.name}
              muscleGroup={ex.muscleGroup}
              sets={ex.sets}
              sessionMaxWeight={sessionMaxWeight}
              onOpenProgress={() => setSheetExercise(ex.name)}
            />
          ))}
        </div>

        {/* ─── Repeat session button ─── */}
        <button
          onClick={() => navigate(`/workouts/${session.workout_id}/session/${session.training_day_id}`)}
          style={{
            width: '100%',
            height: '54px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg,#2BE581,#1fbd6a)',
            border: 'none',
            color: 'rgb(6,33,15)',
            fontSize: '16px',
            fontWeight: 700,
            fontFamily: "'Barlow', sans-serif",
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            boxShadow: '0 8px 24px rgba(43,229,129,0.3)',
          }}
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="rgb(6,33,15)"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
            <path d="M3 3v5h5" />
          </svg>
          Repetir esta sesión
        </button>
      </div>

      {/* ─── Progress sheet ─── */}
      {sheetExercise !== null && (
        <ExerciseProgressSheet
          exerciseName={sheetExercise}
          sessions={allSessions}
          onClose={() => setSheetExercise(null)}
        />
      )}
    </>
  );
}
