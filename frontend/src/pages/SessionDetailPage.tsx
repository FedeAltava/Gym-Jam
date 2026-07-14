import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useSessionHistory } from '../hooks/useSessionHistory';
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

/** Group logs by exercise_name and preserve set order. */
function groupByExercise(
  logs: SessionHistoryLogResponse[],
): Array<{ name: string; sets: SessionHistoryLogResponse[] }> {
  const map = new Map<string, SessionHistoryLogResponse[]>();
  for (const log of logs) {
    const existing = map.get(log.exercise_name);
    if (existing) {
      existing.push(log);
    } else {
      map.set(log.exercise_name, [log]);
    }
  }
  return Array.from(map.entries()).map(([name, sets]) => ({
    name,
    sets: [...sets].sort((a, b) => a.set_number - b.set_number),
  }));
}

// ---------------------------------------------------------------------------
// StatTile (local — mirrors ProfilePage style with string values)
// ---------------------------------------------------------------------------

interface StatTileProps {
  value: string;
  label: string;
}

function StatTile({ value, label }: StatTileProps) {
  return (
    <div
      style={{
        flex: 1,
        padding: '16px 10px',
        borderRadius: '18px',
        background: '#111511',
        border: '1px solid rgba(255,255,255,0.07)',
        textAlign: 'center',
      }}
    >
      <div
        style={{
          fontSize: '22px',
          fontWeight: 800,
          color: 'var(--neon-green)',
          fontFamily: "'Barlow Semi Condensed', sans-serif",
          lineHeight: 1,
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontSize: '11px',
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
  sets: SessionHistoryLogResponse[];
}

function ExerciseCard({ name, sets }: ExerciseCardProps) {
  return (
    <div
      style={{
        background: '#111511',
        borderRadius: '20px',
        border: '1px solid rgba(255,255,255,0.07)',
        padding: '16px',
      }}
    >
      {/* Exercise header */}
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
            fontSize: '12px',
            color: 'var(--text-muted)',
            fontWeight: 500,
            marginTop: '2px',
          }}
        >
          {sets.length} {sets.length === 1 ? 'serie' : 'series'}
        </div>
      </div>

      {/* Set rows */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {sets.map((set) => (
          <div
            key={set.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            {/* Serie label */}
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

            {/* Reps chip */}
            <span
              style={{
                fontSize: '13px',
                fontWeight: 700,
                color: 'var(--text)',
                background: 'rgba(255,255,255,0.06)',
                padding: '4px 10px',
                borderRadius: '8px',
                minWidth: '60px',
                textAlign: 'center',
              }}
            >
              {set.reps_completed} reps
            </span>

            {/* Weight chip */}
            <span
              style={{
                fontSize: '13px',
                fontWeight: 700,
                color: 'var(--text)',
                background: 'rgba(255,255,255,0.06)',
                padding: '4px 10px',
                borderRadius: '8px',
                minWidth: '60px',
                textAlign: 'center',
              }}
            >
              {set.weight_kg != null ? `${set.weight_kg} kg` : '— kg'}
            </span>
          </div>
        ))}
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

  const { data: historyData, isLoading } = useSessionHistory({ status: 'completed' });

  const session = historyData?.pages.flat().find((s) => s.id === sessionId);

  // Loading state
  if (isLoading && !session) {
    return <Spinner />;
  }

  // Not found after load
  if (!isLoading && !session) {
    return (
      <div style={{ textAlign: 'center', padding: '48px 0' }}>
        <p
          style={{
            fontSize: '16px',
            color: 'var(--text-muted)',
            marginBottom: '20px',
          }}
        >
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

  if (!session) {
    return <Spinner />;
  }

  const volume = computeVolume(session.logs);
  const exercises = groupByExercise(session.logs);
  const dayLabel = toDayLabel(session.day_of_week);
  const dateLabel = formatLongDate(session.started_at);
  const durationLabel = formatDuration(session.duration_seconds);
  const prLabel = session.pr_count > 0
    ? `${session.pr_count} ${session.pr_count === 1 ? 'PR' : 'PRs'}`
    : '0 PRs';

  return (
    <div style={{ paddingBottom: '32px' }}>
      {/* ─── Header ─── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px',
          marginBottom: '20px',
        }}
      >
        <button
          onClick={() => navigate(-1)}
          aria-label="Volver"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '36px',
            height: '36px',
            borderRadius: '12px',
            background: 'rgba(255,255,255,0.06)',
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
          <div
            style={{
              fontSize: '13px',
              color: 'var(--text-muted)',
              fontWeight: 500,
              marginTop: '3px',
            }}
          >
            {dayLabel} · {dateLabel} · completada
          </div>
        </div>
      </div>

      {/* ─── Stats bar ─── */}
      <div
        style={{
          display: 'flex',
          gap: '10px',
          marginBottom: '20px',
        }}
      >
        <StatTile value={`${Math.round(volume).toLocaleString('es-ES')} kg`} label="Volumen kg" />
        <StatTile value={durationLabel} label="Duración" />
        <StatTile value={prLabel} label="Récords" />
      </div>

      {/* ─── Exercise list ─── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
        {exercises.map((ex) => (
          <ExerciseCard key={ex.name} name={ex.name} sets={ex.sets} />
        ))}
      </div>

      {/* ─── Repeat session button ─── */}
      <button
        onClick={() =>
          navigate(`/workouts/${session.workout_id}/session/${session.training_day_id}`)
        }
        style={{
          width: '100%',
          height: '52px',
          borderRadius: '16px',
          background: 'var(--neon-green)',
          border: 'none',
          color: 'rgb(6,33,15)',
          fontSize: '16px',
          fontWeight: 700,
          fontFamily: "'Barlow Semi Condensed', sans-serif",
          cursor: 'pointer',
          letterSpacing: '0.3px',
        }}
      >
        Repetir esta sesión
      </button>
    </div>
  );
}
