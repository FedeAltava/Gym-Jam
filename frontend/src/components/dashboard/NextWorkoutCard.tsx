import { Link } from 'react-router-dom';
import { Play, Plus } from 'lucide-react';
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
      <section className="bg-card rounded-card border border-dashed border-border p-6 text-center">
        <p className="font-semibold text-text mb-1">Crea tu primera rutina</p>
        <p className="text-sm text-muted mb-4">
          Planifica tus días de entrenamiento para empezar a progresar
        </p>
        <Link
          to="/workouts?new=true"
          className="inline-flex items-center gap-1.5 h-10 px-4 font-semibold no-underline rounded-btn bg-accent text-bg text-sm neon-glow"
        >
          <Plus size={16} />
          Nueva rutina
        </Link>
      </section>
    );
  }

  const next = resolveNextDay(workout);

  return (
    <section className="bg-card rounded-card border border-border-accent p-5">
      <p className="text-sm text-muted">Próximo entrenamiento</p>
      <p className="font-condensed font-bold text-xl text-text mt-1">{workout.name}</p>
      {next ? (
        <>
          <p className="text-sm text-accent mt-0.5">
            {next.offset === 0
              ? `Hoy · ${DAY_LABEL[next.day.day_of_week as DayKey]}`
              : DAY_LABEL[next.day.day_of_week as DayKey]}
          </p>
          <Link
            to={`/workouts/${workout.id}/session/${next.day.id}`}
            className="mt-4 inline-flex items-center gap-1.5 h-10 px-4 font-semibold no-underline rounded-btn bg-accent text-bg text-sm neon-glow"
          >
            <Play size={16} />
            Empezar sesión
          </Link>
        </>
      ) : (
        <>
          <p className="text-sm text-muted mt-0.5">Sin días de entrenamiento aún</p>
          <Link
            to={`/workouts/${workout.id}`}
            className="mt-4 inline-flex items-center gap-1.5 h-10 px-4 font-semibold no-underline rounded-btn border border-accent text-accent bg-transparent text-sm"
          >
            <Plus size={16} />
            Añadir días
          </Link>
        </>
      )}
    </section>
  );
}
