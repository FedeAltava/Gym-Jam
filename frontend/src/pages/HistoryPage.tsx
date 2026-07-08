import { Link } from 'react-router-dom';
import { Spinner } from '../components/Spinner';
import { useSessionHistory } from '../hooks/useSessionHistory';
import { DAY_LABEL } from '../lib/days';
import type { DayKey } from '../lib/days';
import type { SessionHistoryItemResponse } from '../types/api';
import { useState } from 'react';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const dateFormatter = new Intl.DateTimeFormat('es-ES', { dateStyle: 'medium' });

function formatDate(iso: string): string {
  return dateFormatter.format(new Date(iso));
}

function toDayLabel(day: string): string {
  return DAY_LABEL[day as DayKey] ?? day;
}

function formatDuration(seconds: number | null): string | null {
  if (seconds === null || seconds < 0) return null;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}min`;
  if (m > 0) return `${m}min`;
  return `${seconds}s`;
}

// ---------------------------------------------------------------------------
// Flat SessionCard
// ---------------------------------------------------------------------------

interface SessionCardProps {
  session: SessionHistoryItemResponse;
}

function SessionCard({ session }: SessionCardProps) {
  const duration = formatDuration(session.duration_seconds);

  // Collect unique exercise names from logs (preserve insertion order)
  const exerciseNames: string[] = [];
  const seen = new Set<string>();
  for (const log of session.logs) {
    if (!seen.has(log.exercise_name)) {
      seen.add(log.exercise_name);
      exerciseNames.push(log.exercise_name);
    }
  }
  const visibleExercises = exerciseNames.slice(0, 3);
  const remainder = exerciseNames.length - visibleExercises.length;

  return (
    <div className="rounded-card border border-border bg-card px-4 py-3 space-y-2">
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-text leading-tight truncate">
            {session.workout_name}
          </p>
          <p className="text-xs text-muted mt-0.5">
            {toDayLabel(session.day_of_week)} · {formatDate(session.started_at)}
            {duration && <> · {duration}</>}
          </p>
        </div>

        {/* PR badge */}
        {session.pr_count > 0 && (
          <span
            className="shrink-0 text-xs font-bold px-2 py-0.5 rounded-full border border-accent text-accent neon-glow"
            aria-label={`${session.pr_count} récord${session.pr_count > 1 ? 's' : ''} personal`}
          >
            PR
          </span>
        )}
      </div>

      {/* Exercise chips */}
      {visibleExercises.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {visibleExercises.map((name) => (
            <span
              key={name}
              className="text-xs px-2 py-0.5 rounded-full bg-elevated text-muted border border-border"
            >
              {name}
            </span>
          ))}
          {remainder > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-elevated text-muted border border-border">
              +{remainder}
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

type PeriodValue = '' | 'this_week';

const PERIOD_OPTIONS: { value: PeriodValue; label: string }[] = [
  { value: '', label: 'Todas' },
  { value: 'this_week', label: 'Esta semana' },
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
  const sessions = data
    ? Array.from(
        new Map(data.pages.flat().map((s) => [s.id, s])).values(),
      )
    : undefined;

  const filtersActive = period !== '';

  function clearFilters() {
    setPeriod('');
  }

  return (
    <div>
      {/* Page title */}
      <div className="mb-6">
        <h1 className="font-bold text-2xl text-text">Historial</h1>
        <p className="text-sm mt-0.5 text-muted">
          Todas tus sesiones de entrenamiento
        </p>
      </div>

      {/* Filter chips */}
      <div className="flex gap-1.5 mb-5">
        {PERIOD_OPTIONS.map(({ value, label }) => {
          const active = period === value;
          return (
            <button
              key={value}
              onClick={() => setPeriod(value)}
              className={[
                'text-xs font-semibold px-3 rounded-full border transition-colors',
                active
                  ? 'bg-accent text-bg border-accent'
                  : 'bg-transparent text-muted border-border hover:text-text',
              ].join(' ')}
              style={{ height: '28px', cursor: 'pointer' }}
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
        <div className="space-y-3">
          {sessions.map((session) => (
            <SessionCard key={session.id} session={session} />
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
            No hay sesiones esta semana
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
