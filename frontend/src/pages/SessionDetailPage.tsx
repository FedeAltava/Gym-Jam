import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
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
// ExerciseCard
// ---------------------------------------------------------------------------

interface ExerciseCardProps {
  name: string;
  muscleGroup: string | null;
  sets: SessionHistoryLogResponse[];
  hasPrs: boolean;
}

function ExerciseCard({ name, muscleGroup, sets, hasPrs }: ExerciseCardProps) {
  const maxWeight = hasPrs
    ? Math.max(...sets.map((s) => s.weight_kg ?? 0))
    : -1;

  return (
    <div
      style={{
        background: '#111511',
        borderRadius: '20px',
        border: '1px solid rgba(255,255,255,0.07)',
        padding: '16px',
      }}
    >
      <div style={{ marginBottom: '12px' }}>
        <div
          style={{
            fontSize: '17px',
            fontWeight: 700,
            color: 'var(--text)',
            fontFamily: "'Barlow Semi Condensed', sans-serif",
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
          {muscleGroup ? `${muscleGroup} · ` : ''}{sets.length} {sets.length === 1 ? 'serie' : 'series'}
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {sets.map((set) => {
          const isPr = hasPrs && set.weight_kg != null && set.weight_kg === maxWeight;
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
              <span
                style={{
                  flex: 1,
                  fontSize: '14px',
                  fontWeight: 700,
                  color: 'var(--text)',
                }}
              >
                {set.reps_completed} reps
              </span>
              <span
                style={{
                  fontSize: '14px',
                  fontWeight: 700,
                  color: 'var(--text)',
                }}
              >
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

  const { data: session, isLoading } = useSessionDetail(sessionId);

  // History is used ONLY to find the previous session of the same workout —
  // never to resolve the session being viewed (that comes from useSessionDetail
  // so sessions older than the first history page still load).
  const { data: historyData } = useSessionHistory({ status: 'completed' });
  const allSessions = historyData?.pages.flat() ?? [];

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
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2BE581" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 3v18h18" /><path d="M7 15l4-4 3 3 5-6" />
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
            hasPrs={session.pr_count > 0}
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
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgb(6,33,15)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" />
        </svg>
        Repetir esta sesión
      </button>
    </div>
  );
}
