import { DAY_LABEL, type DayKey } from '../../lib/days';
import type { SessionHistoryItemResponse } from '../../types/api';

interface RecentActivityListProps {
  /** Already limited to the sessions to display (most recent first). */
  sessions: SessionHistoryItemResponse[];
}

const dateFormat = new Intl.DateTimeFormat('es-ES', { day: 'numeric', month: 'short' });

export function RecentActivityList({ sessions }: RecentActivityListProps) {
  return (
    <section>
      <h2 className="font-semibold text-base text-text mb-3">Actividad reciente</h2>
      {sessions.length === 0 ? (
        <p className="text-sm text-muted">Aún no has completado ningún entrenamiento</p>
      ) : (
        <div className="grid gap-3">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="bg-card rounded-card border border-border p-4 flex items-center justify-between"
            >
              <div>
                <p className="font-semibold text-sm text-text">{session.workout_name}</p>
                <p className="text-xs text-muted mt-0.5">
                  {DAY_LABEL[session.day_of_week as DayKey] ?? session.day_of_week} ·{' '}
                  {dateFormat.format(new Date(session.started_at))}
                </p>
              </div>
              <span className="text-xs text-muted">
                {session.logs.length} {session.logs.length === 1 ? 'serie' : 'series'}
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
