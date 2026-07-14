import { Link } from 'react-router-dom';
import { Spinner } from '../components/Spinner';
import { useSessionHistory } from '../hooks/useSessionHistory';
import { DAY_SHORT } from '../lib/days';
import type { DayKey } from '../lib/days';
import type { SessionHistoryItemResponse } from '../types/api';
import { useState } from 'react';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const shortDateFormatter = new Intl.DateTimeFormat('es-ES', {
  day: 'numeric',
  month: 'short',
});

function formatShortDate(iso: string): string {
  return shortDateFormatter.format(new Date(iso));
}

function toDayShort(day: string): string {
  return DAY_SHORT[day as DayKey] ?? day;
}

function formatDuration(seconds: number | null): string | null {
  if (seconds === null || seconds < 0) return null;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}min`;
  if (m > 0) return `${m}min`;
  return `${seconds}s`;
}

/** Compute total volume (kg) from session logs. */
function computeVolume(logs: SessionHistoryItemResponse['logs']): number {
  return logs.reduce((sum, l) => sum + (l.weight_kg ?? 0) * l.reps_completed, 0);
}

/** Group logs by exercise_name and build "Name Nsets×reps" chips (max 3). */
function buildExerciseChips(logs: SessionHistoryItemResponse['logs']): {
  chips: string[];
  remainder: number;
} {
  // Group by exercise_name — track set count and last reps value
  const groupMap = new Map<string, { sets: number; reps: number }>();
  for (const log of logs) {
    const entry = groupMap.get(log.exercise_name);
    if (entry) {
      entry.sets += 1;
      entry.reps = log.reps_completed;
    } else {
      groupMap.set(log.exercise_name, { sets: 1, reps: log.reps_completed });
    }
  }

  const allChips = Array.from(groupMap.entries()).map(
    ([name, { sets, reps }]) => `${name} ${sets}×${reps}`,
  );

  const chips = allChips.slice(0, 3);
  const remainder = allChips.length - chips.length;
  return { chips, remainder };
}

// ---------------------------------------------------------------------------
// SessionCard
// ---------------------------------------------------------------------------

interface SessionCardProps {
  session: SessionHistoryItemResponse;
  isFirst: boolean;
}

function SessionCard({ session, isFirst }: SessionCardProps) {
  const volume = computeVolume(session.logs);
  const { chips, remainder } = buildExerciseChips(session.logs);

  const dayShort = toDayShort(session.day_of_week);
  const dateShort = formatShortDate(session.started_at);
  const exerciseCount = new Set(session.logs.map((l) => l.exercise_name)).size;
  const duration = formatDuration(session.duration_seconds);

  // Subtitle: "Lun · 7 jul · 4 ejercicios [· duration]"
  const subtitle = [
    `${dayShort} · ${dateShort}`,
    `${exerciseCount} ejercicio${exerciseCount !== 1 ? 's' : ''}`,
    ...(duration ? [duration] : []),
  ].join(' · ');

  return (
    <div
      style={{
        borderRadius: '20px',
        padding: '18px',
        background: isFirst ? '#111511' : 'rgb(15,19,15)',
        border: isFirst ? '1px solid rgba(255,255,255,0.07)' : '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: chips.length > 0 ? '12px' : 0,
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: '16px',
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
              fontSize: '12px',
              color: 'var(--text-muted)',
              fontWeight: 500,
              marginTop: '2px',
            }}
          >
            {subtitle}
          </div>
        </div>

        {/* Volume or PR badge */}
        <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: '12px' }}>
          {session.pr_count > 0 ? (
            <div>
              <div
                style={{
                  fontSize: '18px',
                  fontWeight: 800,
                  color: isFirst ? 'var(--neon-green)' : 'var(--text)',
                  fontFamily: "'Barlow Semi Condensed', sans-serif",
                }}
                aria-label={`${session.pr_count} récord${session.pr_count > 1 ? 's' : ''} personal`}
              >
                PR
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>
                {session.pr_count}×
              </div>
            </div>
          ) : volume > 0 ? (
            <div>
              <div
                style={{
                  fontSize: '18px',
                  fontWeight: 800,
                  color: isFirst ? 'var(--neon-green)' : 'var(--text)',
                  fontFamily: "'Barlow Semi Condensed', sans-serif",
                }}
              >
                {Math.round(volume).toLocaleString('es-ES')}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>
                kg
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {/* Exercise chips */}
      {chips.length > 0 && (
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {chips.map((chip) => (
            <span
              key={chip}
              style={{
                fontSize: '12px',
                color: 'rgb(159,176,162)',
                fontWeight: 600,
                background: 'rgba(255,255,255,0.05)',
                padding: '5px 10px',
                borderRadius: '10px',
              }}
            >
              {chip}
            </span>
          ))}
          {remainder > 0 && (
            <span
              style={{
                fontSize: '12px',
                color: 'rgb(159,176,162)',
                fontWeight: 600,
                background: 'rgba(255,255,255,0.05)',
                padding: '5px 10px',
                borderRadius: '10px',
              }}
            >
              +{remainder} más
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Period filter options
// ---------------------------------------------------------------------------

type PeriodValue = '' | 'this_week' | 'pr';

interface PeriodOption {
  value: PeriodValue;
  label: string;
}

const PERIOD_OPTIONS: PeriodOption[] = [
  { value: '', label: 'Todas' },
  { value: 'this_week', label: 'Esta semana' },
  { value: 'pr', label: 'PRs' },
];

// ---------------------------------------------------------------------------
// HistoryPage
// ---------------------------------------------------------------------------

export function HistoryPage() {
  const [period, setPeriod] = useState<PeriodValue>('');

  const {
    data,
    isLoading,
    isError,
    error,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = useSessionHistory({
    period: period === 'this_week' ? 'this_week' : undefined,
  });

  // Deduplicate sessions across pages
  const allSessions = data
    ? Array.from(
        new Map(data.pages.flat().map((s) => [s.id, s])).values(),
      )
    : undefined;

  // Client-side filter for PRs
  const sessions =
    period === 'pr'
      ? allSessions?.filter((s) => s.pr_count > 0)
      : allSessions;

  const filtersActive = period !== '';

  function clearFilters() {
    setPeriod('');
  }

  return (
    <div>
      {/* Page title */}
      <div>
        <div style={{ fontSize: '27px', fontWeight: 700, color: 'var(--text)', fontFamily: "'Barlow Semi Condensed', sans-serif", marginBottom: '2px' }}>
          Historial
        </div>
        <div style={{ fontSize: '14px', color: 'var(--text-muted)', fontWeight: 500, marginBottom: '18px' }}>
          Todas tus sesiones de entrenamiento
        </div>
      </div>

      {/* Filter chips */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {PERIOD_OPTIONS.map(({ value, label }) => {
          const active = period === value;
          return (
            <button
              key={value}
              onClick={() => setPeriod(value)}
              style={{
                fontSize: '13px',
                fontWeight: active ? 700 : 600,
                color: active ? 'rgb(6,33,15)' : 'rgb(159,176,162)',
                background: active ? 'var(--neon-green)' : 'rgba(255,255,255,0.05)',
                padding: '8px 16px',
                borderRadius: '20px',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Loading state */}
      {isLoading && <Spinner />}

      {/* Error state */}
      {isError && (
        <p className="text-sm text-danger">
          Error: {(error as Error).message}
        </p>
      )}

      {/* Session list */}
      {sessions && sessions.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {sessions.map((session, index) => (
            <Link
              key={session.id}
              to={`/history/${session.id}`}
              style={{ textDecoration: 'none' }}
            >
              <SessionCard session={session} isFirst={index === 0} />
            </Link>
          ))}
        </div>
      )}

      {/* Empty states */}
      {sessions?.length === 0 && !filtersActive && (
        <div className="text-center py-16 rounded-card border-2 border-dashed border-border">
          <p className="text-3xl mb-3">📋</p>
          <p className="font-semibold mb-1 text-text">
            Aún no tienes sesiones registradas
          </p>
          <p className="text-sm text-muted mb-4">
            Completa tu primer entrenamiento para verlo aquí
          </p>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-1.5 text-sm font-semibold no-underline rounded-btn bg-accent text-bg"
            style={{ height: '36px', padding: '0 16px' }}
          >
            Ir al inicio
          </Link>
        </div>
      )}

      {sessions?.length === 0 && filtersActive && (
        <div className="text-center py-16 rounded-card border-2 border-dashed border-border">
          <p className="text-3xl mb-3">🔍</p>
          <p className="font-semibold mb-1 text-text">
            No hay sesiones en este filtro
          </p>
          <button
            onClick={clearFilters}
            className="mt-3 inline-flex items-center text-sm font-semibold rounded-btn border border-accent text-accent bg-transparent transition-colors hover:bg-accent hover:text-bg"
            style={{ height: '36px', padding: '0 16px', cursor: 'pointer' }}
          >
            Ver todas
          </button>
        </div>
      )}

      {/* Load more */}
      {hasNextPage && (
        <div className="flex justify-center mt-6">
          <button
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
            className="inline-flex items-center gap-2 text-sm font-semibold rounded-btn border border-accent text-accent bg-transparent transition-colors hover:bg-accent hover:text-bg disabled:opacity-60 disabled:pointer-events-none"
            style={{ height: '40px', padding: '0 20px', cursor: 'pointer' }}
          >
            {isFetchingNextPage ? 'Cargando…' : 'Cargar más'}
          </button>
        </div>
      )}
    </div>
  );
}
