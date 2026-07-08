import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Play, Plus } from 'lucide-react';
import { useWorkouts } from '../hooks/useWorkouts';
import { Spinner } from '../components/Spinner';
import { NewRoutineModal } from '../components/workouts/NewRoutineModal';
import { DAYS, DAY_LABEL, DAY_SHORT, mondayFirstIndex, type DayKey } from '../lib/days';
import type { WorkoutResponse } from '../types/api';

function exerciseCount(workout: WorkoutResponse): number {
  return workout.training_days.reduce((total, day) => total + day.exercises.length, 0);
}

function RoutineCard({
  workout,
  todayKey,
}: {
  workout: WorkoutResponse;
  todayKey: DayKey;
}) {
  const count = exerciseCount(workout);
  const todayPlanDay = workout.is_active
    ? workout.training_days.find((d) => d.day_of_week === todayKey)
    : undefined;

  return (
    <article className="relative rounded-card border border-border bg-card p-4 transition-colors hover:border-border-accent">
      <div className="flex items-start justify-between gap-2">
        {/* Stretched link: the whole card navigates to the detail page. */}
        <Link
          to={`/workouts/${workout.id}`}
          className="no-underline flex-1 min-w-0 after:absolute after:inset-0 after:content-['']"
        >
          <h3 className="font-condensed font-bold text-lg text-text truncate">
            {workout.name}
          </h3>
        </Link>
        {workout.is_active && (
          <span className="shrink-0 text-xs font-semibold px-2 py-0.5 rounded-full bg-[var(--accent-soft)] border border-border-accent text-accent">
            Activo
          </span>
        )}
      </div>

      {workout.description && (
        <p className="text-sm mt-1 line-clamp-2 text-muted">{workout.description}</p>
      )}

      <div className="flex flex-wrap items-center gap-1.5 mt-3">
        <span className="text-xs font-semibold px-2 py-0.5 rounded-full border border-border text-muted">
          {count} ejercicio{count !== 1 ? 's' : ''}
        </span>
        {workout.training_days.length === 0 ? (
          <span className="text-xs italic text-muted">Sin días asignados</span>
        ) : (
          workout.training_days.map((d) => (
            <span
              key={d.id}
              className="text-xs font-semibold px-2 py-0.5 rounded-full border border-border text-muted"
            >
              {DAY_SHORT[d.day_of_week as DayKey] ?? d.day_of_week}
            </span>
          ))
        )}
      </div>

      {todayPlanDay && (
        <Link
          to={`/workouts/${workout.id}/session/${todayPlanDay.id}`}
          className="relative z-10 mt-4 inline-flex items-center gap-1.5 h-10 px-4 font-semibold no-underline rounded-btn bg-accent text-bg text-sm neon-glow"
        >
          <Play size={16} />
          Empezar hoy · {DAY_LABEL[todayKey]}
        </Link>
      )}
    </article>
  );
}

export function WorkoutsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [showModal, setShowModal] = useState(() => searchParams.get('new') === 'true');

  useEffect(() => {
    if (searchParams.get('new') === 'true') {
      setShowModal(true);
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);
  const {
    data,
    isLoading,
    isError,
    error,
    hasNextPage,
    fetchNextPage,
    isFetchingNextPage,
  } = useWorkouts();

  // Offset pagination can repeat items between pages — dedupe by id.
  const workouts = data
    ? Array.from(new Map(data.pages.flat().map((w) => [w.id, w])).values())
    : [];
  const todayKey = DAYS[mondayFirstIndex(new Date())];

  return (
    <div>
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-condensed font-bold text-2xl text-text">Rutinas</h1>
          <p className="text-sm mt-0.5 text-muted">Tus planes de entrenamiento</p>
        </div>
        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-1.5 h-10 px-4 font-semibold rounded-btn bg-accent text-bg text-sm neon-glow"
          style={{ border: 'none', cursor: 'pointer' }}
        >
          <Plus size={16} />
          Nueva rutina
        </button>
      </header>

      {isLoading ? (
        <Spinner />
      ) : isError ? (
        <p className="text-sm text-danger">Error: {(error as Error).message}</p>
      ) : workouts.length === 0 ? (
        <div className="rounded-card border border-dashed border-border bg-card p-8 text-center">
          <p className="font-semibold text-text mb-1">Sin rutinas todavía</p>
          <p className="text-sm text-muted mb-4">
            Crea tu primera rutina para planificar tus entrenamientos
          </p>
          <button
            type="button"
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-1.5 h-10 px-4 font-semibold rounded-btn bg-accent text-bg text-sm neon-glow"
            style={{ border: 'none', cursor: 'pointer' }}
          >
            <Plus size={16} />
            Crear rutina
          </button>
        </div>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            {workouts.map((w) => (
              <RoutineCard key={w.id} workout={w} todayKey={todayKey} />
            ))}
          </div>
          {hasNextPage && (
            <div className="mt-4 text-center">
              <button
                type="button"
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
                className="text-sm font-semibold rounded-btn border border-border text-muted transition-colors hover:text-text disabled:opacity-60"
                style={{
                  height: '36px',
                  padding: '0 16px',
                  backgroundColor: 'transparent',
                  cursor: 'pointer',
                }}
              >
                {isFetchingNextPage ? 'Cargando…' : 'Cargar más'}
              </button>
            </div>
          )}
        </>
      )}

      {showModal && <NewRoutineModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
