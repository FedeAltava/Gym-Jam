import { Link } from 'react-router-dom';
import type { WorkoutResponse } from '../types/api';
import { DAY_SHORT } from '../lib/days';

export function WorkoutCard({ workout }: { workout: WorkoutResponse }) {
  return (
    <Link to={`/workouts/${workout.id}`} className="block no-underline">
      <div
        className={[
          'transition-all duration-200 hover:scale-[1.02]',
          'rounded-card border border-border bg-surface',
          'border-l-4 border-l-accent p-4 mb-3',
          'shadow-[0_2px_8px_rgba(0,0,0,0.3)]',
          'hover:shadow-[0_4px_20px_rgba(0,255,135,0.15)]',
        ].join(' ')}
      >
        <h3 className="font-bold mb-1 text-base text-text">{workout.name}</h3>
        {workout.description && (
          <p className="text-sm mb-3 line-clamp-2 text-muted">
            {workout.description}
          </p>
        )}
        <div className="flex flex-wrap gap-1.5 mt-2">
          {workout.training_days.map((d) => (
            <span
              key={d.day_of_week}
              className="text-xs font-semibold px-2 py-0.5 rounded-full text-accent"
              style={{
                backgroundColor: 'rgba(0, 255, 135, 0.1)',
                border: '1px solid rgba(0, 255, 135, 0.3)',
              }}
            >
              {DAY_SHORT[d.day_of_week as keyof typeof DAY_SHORT] ?? d.day_of_week}
            </span>
          ))}
          {workout.training_days.length === 0 && (
            <span className="text-xs italic text-muted">Sin días asignados</span>
          )}
        </div>
      </div>
    </Link>
  );
}
