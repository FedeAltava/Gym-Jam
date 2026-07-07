import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Spinner } from '../components/Spinner';
import { useSessionHistory } from '../hooks/useSessionHistory';
import { useWorkouts } from '../hooks/useWorkouts';
import { DAY_LABEL } from '../lib/days';
import type { DayKey } from '../lib/days';
import type { SessionHistoryItemResponse } from '../types/api';

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

function computeTotalVolume(
  logs: SessionHistoryItemResponse['logs'],
): number {
  return logs.reduce((sum, log) => {
    if (log.weight_kg === null) return sum;
    return sum + log.reps_completed * log.weight_kg;
  }, 0);
}

// ---------------------------------------------------------------------------
// SessionCard — single collapsible card
// ---------------------------------------------------------------------------

interface SessionCardProps {
  session: SessionHistoryItemResponse;
}

function SessionCard({ session }: SessionCardProps) {
  const [expanded, setExpanded] = useState(false);

  const totalVolume = computeTotalVolume(session.logs);
  const isCompleted = session.status === 'completed';

  // Group logs by exercise_name for the expanded view
  const byExercise = session.logs.reduce<
    Record<string, SessionHistoryItemResponse['logs']>
  >((acc, log) => {
    (acc[log.exercise_name] ??= []).push(log);
    return acc;
  }, {});

  return (
    <div
      className="rounded-card border border-border bg-surface"
      style={{ overflow: 'hidden' }}
    >
      {/* Collapsed header — always visible */}
      <button
        onClick={() => setExpanded((prev) => !prev)}
        className="w-full text-left px-4 py-3"
        style={{ background: 'none', border: 'none', cursor: 'pointer' }}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-sm text-text">
                {session.workout_name}
              </span>
              <span
                className={[
                  'text-xs font-semibold px-2 py-0.5 rounded-full',
                  isCompleted
                    ? 'bg-green-900/40 text-green-400'
                    : 'bg-orange-900/40 text-orange-400',
                ].join(' ')}
              >
                {isCompleted ? 'Completado' : 'En curso'}
              </span>
            </div>
            <p className="text-xs text-muted mt-0.5">
              {toDayLabel(session.day_of_week)} ·{' '}
              {formatDate(session.started_at)}
            </p>
          </div>
          {/* Chevron */}
          <span
            className="text-muted shrink-0"
            style={{
              display: 'inline-block',
              transition: 'transform 0.2s',
              transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
              fontSize: '12px',
            }}
          >
            ▾
          </span>
        </div>

        {/* Summary line */}
        <p className="text-xs text-muted mt-1">
          {session.logs.length} series
          {totalVolume > 0 && (
            <> · {totalVolume.toFixed(0)} kg</>
          )}
        </p>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-border pt-3">
          {Object.entries(byExercise).map(([exerciseName, logs]) => (
            <div key={exerciseName}>
              <p className="text-xs font-semibold text-text mb-1">
                {exerciseName}
              </p>
              <div className="space-y-0.5">
                {logs.map((log) => (
                  <p key={log.id} className="text-xs text-muted">
                    Serie {log.set_number} · {log.reps_completed} reps ·{' '}
                    {log.weight_kg !== null
                      ? `${log.weight_kg} kg`
                      : 'Peso corporal'}
                  </p>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// HistoryPage
// ---------------------------------------------------------------------------

const STATUS_OPTIONS = [
  { value: '', label: 'Todas' },
  { value: 'completed', label: 'Completadas' },
  { value: 'in_progress', label: 'En curso' },
];

export function HistoryPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const workoutId = searchParams.get('workout') ?? '';
  const status = searchParams.get('status') ?? '';

  const filtersActive = Boolean(workoutId || status);

  const {
    data,
    isLoading,
    isError,
    error,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = useSessionHistory({
    workoutId: workoutId || undefined,
    status: status || undefined,
  });

  // First page of workouts for the filter dropdown
  const { data: workoutsData } = useWorkouts();
  const allWorkouts = workoutsData?.pages[0] ?? [];

  // Deduplicate sessions across pages (same as DashboardPage pattern)
  const sessions = data
    ? Array.from(
        new Map(data.pages.flat().map((s) => [s.id, s])).values(),
      )
    : undefined;

  function handleWorkoutChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const next = new URLSearchParams(searchParams);
    if (e.target.value) {
      next.set('workout', e.target.value);
    } else {
      next.delete('workout');
    }
    setSearchParams(next);
  }

  function handleStatusChange(value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set('status', value);
    } else {
      next.delete('status');
    }
    setSearchParams(next);
  }

  function clearFilters() {
    setSearchParams({});
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

      {/* Filter bar — column on mobile so the native select never overlaps chips */}
      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center mb-5">
        {/* Workout dropdown */}
        <select
          value={workoutId}
          onChange={handleWorkoutChange}
          className="w-full sm:w-auto text-sm rounded-btn border border-border bg-surface text-text px-3"
          style={{ height: '36px', cursor: 'pointer', colorScheme: 'dark' }}
        >
          <option value="">Todos los planes</option>
          {allWorkouts.map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
        </select>

        {/* Status chips */}
        <div className="flex gap-1.5">
          {STATUS_OPTIONS.map(({ value, label }) => {
            const active = status === value;
            return (
              <button
                key={value}
                onClick={() => handleStatusChange(value)}
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
            No hay sesiones con estos filtros
          </p>
          <button
            onClick={clearFilters}
            className="mt-3 inline-flex items-center text-sm font-semibold rounded-btn border border-accent text-accent bg-transparent transition-colors hover:bg-accent hover:text-bg"
            style={{ height: '36px', padding: '0 16px', cursor: 'pointer' }}
          >
            Limpiar filtros
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
