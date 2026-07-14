import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { DAYS, DAY_LABEL, mondayFirstIndex, type DayKey } from '../../lib/days';
import type { WorkoutResponse, TrainingDayResponse } from '../../types/api';

interface NextWorkoutCardProps {
  workout: WorkoutResponse | undefined;
}

interface NextDay {
  day: TrainingDayResponse;
  offset: number;
}

/** First plan day >= today in Monday-first order, wrapping to next week. */
function resolveNextDay(workout: WorkoutResponse): NextDay | undefined {
  const todayIdx = mondayFirstIndex(new Date());
  let best: NextDay | undefined;
  for (const day of workout.training_days) {
    const dayIdx = DAYS.indexOf(day.day_of_week as DayKey);
    if (dayIdx < 0) continue;
    const offset = (dayIdx - todayIdx + 7) % 7;
    if (!best || offset < best.offset) best = { day, offset };
  }
  return best;
}

export function NextWorkoutCard({ workout }: NextWorkoutCardProps) {
  if (!workout) {
    return (
      <section
        style={{
          borderRadius: '22px',
          padding: '24px',
          background: 'transparent',
          border: '1.5px dashed rgba(255,255,255,0.12)',
          textAlign: 'center',
        }}
      >
        <p style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' }}>
          Crea tu primera rutina
        </p>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Planifica tus días de entrenamiento para empezar a progresar
        </p>
        <Link
          to="/workouts"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            height: '40px',
            padding: '0 16px',
            fontWeight: 600,
            textDecoration: 'none',
            borderRadius: '12px',
            background: 'linear-gradient(135deg,#2BE581,#1fbd6a)',
            color: 'rgb(6,33,15)',
            fontSize: '14px',
          }}
        >
          <Plus size={16} />
          Nueva rutina
        </Link>
      </section>
    );
  }

  const next = resolveNextDay(workout);

  const dayLabel = next
    ? next.offset === 0
      ? `Hoy · ${DAY_LABEL[next.day.day_of_week as DayKey]}`
      : DAY_LABEL[next.day.day_of_week as DayKey]
    : 'Sin días de entrenamiento aún';

  return (
    <section
      style={{
        borderRadius: '22px',
        padding: '20px',
        background: '#111511',
        border: '1px solid rgba(43,229,129,0.25)',
      }}
    >
      {/* Active badge */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '8px' }}>
        <span
          style={{
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
      </div>

      <div
        style={{
          fontFamily: "'Barlow Semi Condensed', sans-serif",
          fontSize: '21px',
          fontWeight: 700,
          color: 'var(--text)',
        }}
      >
        {workout.name}
      </div>
      <div
        style={{
          fontSize: '13px',
          color: 'var(--text-muted)',
          marginTop: '4px',
          marginBottom: next ? '0' : '0',
        }}
      >
        {dayLabel}
      </div>

      {next ? (
        <Link
          to={`/workouts/${workout.id}/session/${next.day.id}`}
          aria-label="Empezar sesión"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            height: '48px',
            padding: '0 20px',
            marginTop: '14px',
            textDecoration: 'none',
            borderRadius: '14px',
            background: 'linear-gradient(135deg,#2BE581,#1fbd6a)',
            color: 'rgb(6,33,15)',
            fontSize: '15px',
            fontWeight: 700,
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5,3 19,12 5,21" />
          </svg>
          {next.offset === 0
            ? `Empezar hoy · ${DAY_LABEL[next.day.day_of_week as DayKey]}`
            : 'Empezar sesión'}
        </Link>
      ) : (
        <Link
          to={`/workouts/${workout.id}`}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            height: '40px',
            padding: '0 16px',
            marginTop: '14px',
            textDecoration: 'none',
            borderRadius: '12px',
            border: '1px solid rgba(43,229,129,0.4)',
            color: '#2BE581',
            background: 'transparent',
            fontSize: '14px',
            fontWeight: 600,
          }}
        >
          <Plus size={16} />
          Añadir días
        </Link>
      )}
    </section>
  );
}
