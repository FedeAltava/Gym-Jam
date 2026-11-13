import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { DAYS, DAY_LABEL, mondayFirstIndex, type DayKey } from '../../lib/days';
import type { WorkoutResponse, TrainingDayResponse } from '../../types/api';

interface NextWorkoutCardProps {
  workout: WorkoutResponse | undefined;
  /** Routine days (day_of_week) with a completed session this week, on any date. */
  trainedDays: ReadonlySet<string>;
}

interface NextDay {
  day: TrainingDayResponse;
  // Where the day falls against today: an earlier weekday still pending,
  // today, later this week, or next week once the whole week is trained.
  when: 'pending' | 'today' | 'later' | 'next-week';
}

/**
 * The earliest routine day not trained yet this week, whatever its weekday:
 * a skipped Monday stays the next workout on Tuesday. Once every routine day
 * is trained, the first one of next week. Also returns today's routine day
 * when it is still pending but is not the next one, to offer it as well.
 */
function resolveNextDay(
  workout: WorkoutResponse,
  trainedDays: ReadonlySet<string>,
): { next?: NextDay; today?: TrainingDayResponse } {
  const todayIdx = mondayFirstIndex(new Date());
  const planDays = workout.training_days
    .filter((day) => DAYS.indexOf(day.day_of_week as DayKey) >= 0)
    .sort((a, b) => DAYS.indexOf(a.day_of_week as DayKey) - DAYS.indexOf(b.day_of_week as DayKey));
  if (planDays.length === 0) return {};

  const pending = planDays.filter((day) => !trainedDays.has(day.day_of_week));
  if (pending.length === 0) return { next: { day: planDays[0], when: 'next-week' } };

  const first = pending[0];
  const firstIdx = DAYS.indexOf(first.day_of_week as DayKey);
  const when = firstIdx < todayIdx ? 'pending' : firstIdx === todayIdx ? 'today' : 'later';
  const today = pending.find((day) => DAYS.indexOf(day.day_of_week as DayKey) === todayIdx);
  return { next: { day: first, when }, today: today !== first ? today : undefined };
}

export function NextWorkoutCard({ workout, trainedDays }: NextWorkoutCardProps) {
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

  const { next, today } = resolveNextDay(workout, trainedDays);
  const nextName = next ? DAY_LABEL[next.day.day_of_week as DayKey] : '';

  const dayLabel = !next
    ? 'Sin días de entrenamiento aún'
    : next.when === 'pending'
      ? `Pendiente · ${nextName}`
      : next.when === 'today'
        ? `Hoy · ${nextName}`
        : next.when === 'next-week'
          ? `Próxima semana · ${nextName}`
          : nextName;

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
        <>
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
            {next.when === 'today'
              ? `Empezar hoy · ${nextName}`
              : next.when === 'pending'
                ? `Empezar · ${nextName}`
                : 'Empezar sesión'}
          </Link>
          {today && (
            <div style={{ marginTop: '10px' }}>
              <Link
                to={`/workouts/${workout.id}/session/${today.id}`}
                aria-label={`Empezar el día de hoy: ${DAY_LABEL[today.day_of_week as DayKey]}`}
                style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)', textDecoration: 'underline' }}
              >
                o hoy toca {DAY_LABEL[today.day_of_week as DayKey]}
              </Link>
            </div>
          )}
        </>
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
