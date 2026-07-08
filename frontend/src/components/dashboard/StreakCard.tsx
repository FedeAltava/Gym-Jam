interface StreakCardProps {
  streak: number;
  /** Monday-first weekday indexes (0–6) that belong to the active plan. */
  planDays: ReadonlySet<number>;
  /** Monday-first weekday indexes with a completed session this week. */
  completedDays: ReadonlySet<number>;
}

function segmentClass(index: number, planDays: ReadonlySet<number>, completedDays: ReadonlySet<number>): string {
  if (planDays.has(index) && completedDays.has(index)) return 'bg-accent';
  if (planDays.has(index)) return 'bg-muted';
  return 'bg-border';
}

export function StreakCard({ streak, planDays, completedDays }: StreakCardProps) {
  return (
    <section className="bg-card rounded-card border border-border p-5">
      <p className="text-sm text-muted">Racha</p>
      <div className="flex items-baseline gap-2 mt-1">
        <span className="font-condensed font-bold text-5xl text-accent leading-none">
          {streak}
        </span>
        <span className="text-sm text-muted">días seguidos</span>
      </div>
      <div className="flex gap-1.5 mt-4" aria-hidden="true">
        {Array.from({ length: 7 }, (_, i) => (
          <div
            key={i}
            className={`h-1.5 flex-1 rounded-full ${segmentClass(i, planDays, completedDays)}`}
          />
        ))}
      </div>
    </section>
  );
}
