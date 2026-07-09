import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
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
  const navigate = useNavigate();
  const count = exerciseCount(workout);
  const todayPlanDay = workout.is_active
    ? workout.training_days.find((d) => d.day_of_week === todayKey)
    : undefined;

  const isActive = workout.is_active;
  const allDays = workout.training_days;
  const visibleDays = allDays.slice(0, 3);
  const extraDays = allDays.length - visibleDays.length;

  return (
    <article
      onClick={() => navigate(`/workouts/${workout.id}`)}
      style={{
        borderRadius: '22px',
        padding: '20px',
        background: isActive ? '#111511' : '#0f130f',
        border: isActive ? '1px solid rgba(43,229,129,0.25)' : '1px solid rgba(255,255,255,0.07)',
        marginBottom: '14px',
        position: 'relative',
        cursor: 'pointer',
      }}
    >
      {/* Header row: name + active badge */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
        <h3
          style={{
            fontSize: '19px',
            fontFamily: "'Barlow Semi Condensed', sans-serif",
            fontWeight: 700,
            color: 'var(--text)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            margin: 0,
            flex: 1,
            minWidth: 0,
          }}
        >
          {workout.name}
        </h3>
        {isActive && (
          <span
            style={{
              flexShrink: 0,
              fontSize: '11px',
              fontWeight: 700,
              color: '#2BE581',
              background: 'rgba(43,229,129,0.12)',
              padding: '3px 10px',
              borderRadius: '20px',
            }}
          >
            Activo
          </span>
        )}
      </div>

      {/* Meta line */}
      <p
        style={{
          fontSize: '13px',
          color: 'var(--text-muted)',
          fontWeight: 500,
          margin: '4px 0 14px',
        }}
      >
        {workout.training_days.length} día{workout.training_days.length !== 1 ? 's' : ''} · {count} ejercicio{count !== 1 ? 's' : ''}
      </p>

      {/* Day chips */}
      {allDays.length > 0 && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
          {visibleDays.map((d) => (
            <span
              key={d.id}
              style={{
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text)',
                background: 'rgba(255,255,255,0.06)',
                padding: '6px 12px',
                borderRadius: '12px',
              }}
            >
              {DAY_SHORT[d.day_of_week as DayKey] ?? d.day_of_week}
            </span>
          ))}
          {extraDays > 0 && (
            <span
              style={{
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-muted)',
                background: 'rgba(255,255,255,0.04)',
                padding: '6px 12px',
                borderRadius: '12px',
              }}
            >
              +{extraDays}
            </span>
          )}
        </div>
      )}

      {/* CTA: start today's session */}
      {todayPlanDay && (
        <Link
          to={`/workouts/${workout.id}/session/${todayPlanDay.id}`}
          onClick={(e) => e.stopPropagation()}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            height: '48px',
            padding: '0 20px',
            textDecoration: 'none',
            border: 'none',
            borderRadius: '14px',
            background: 'linear-gradient(135deg,#2BE581,#1fbd6a)',
            color: 'rgb(6,33,15)',
            fontSize: '15px',
            fontWeight: 700,
          }}
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
      setTimeout(() => setShowModal(true), 0);
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
      {/* Header — no top-right button */}
      <div style={{ marginBottom: '20px' }}>
        <div
          style={{
            fontSize: '27px',
            fontWeight: 700,
            color: 'var(--text)',
            fontFamily: "'Barlow Semi Condensed', sans-serif",
          }}
        >
          Rutinas
        </div>
        <div style={{ fontSize: '14px', color: '#7E8A7E', fontWeight: 500 }}>
          Tus planes de entrenamiento
        </div>
      </div>

      {isLoading ? (
        <Spinner />
      ) : isError ? (
        <p className="text-sm text-danger">Error: {(error as Error).message}</p>
      ) : workouts.length === 0 ? (
        <div
          style={{
            borderRadius: '18px',
            border: '1.5px dashed rgba(43,229,129,0.35)',
            background: 'transparent',
            padding: '32px',
            textAlign: 'center',
          }}
        >
          <p style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>
            Sin rutinas todavía
          </p>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Crea tu primera rutina para planificar tus entrenamientos
          </p>
          <button
            type="button"
            onClick={() => setShowModal(true)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              height: '48px',
              padding: '0 20px',
              border: 'none',
              borderRadius: '14px',
              background: 'linear-gradient(135deg,#2BE581,#1fbd6a)',
              color: 'rgb(6,33,15)',
              fontSize: '15px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            <Plus size={16} />
            Crear rutina
          </button>
        </div>
      ) : (
        <>
          <div>
            {workouts.map((w) => (
              <RoutineCard key={w.id} workout={w} todayKey={todayKey} />
            ))}
          </div>

          {hasNextPage && (
            <div style={{ marginTop: '8px', textAlign: 'center' }}>
              <button
                type="button"
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
                style={{
                  height: '36px',
                  padding: '0 16px',
                  backgroundColor: 'transparent',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: 600,
                  borderRadius: '12px',
                  border: '1px solid rgba(255,255,255,0.12)',
                  color: 'var(--text-muted)',
                }}
              >
                {isFetchingNextPage ? 'Cargando…' : 'Cargar más'}
              </button>
            </div>
          )}

          {/* New routine dashed button at bottom */}
          <button
            type="button"
            onClick={() => setShowModal(true)}
            style={{
              width: '100%',
              height: '54px',
              border: '1.5px dashed rgba(43,229,129,0.35)',
              borderRadius: '18px',
              background: 'transparent',
              color: '#2BE581',
              fontSize: '15px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              marginTop: '8px',
            }}
          >
            <Plus size={18} />
            Nueva rutina
          </button>
        </>
      )}

      {showModal && <NewRoutineModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
