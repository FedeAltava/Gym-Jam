const DAY_LETTERS = ['L', 'M', 'X', 'J', 'V', 'S', 'D'] as const;

interface WeeklyChartProps {
  /** Per-day activity metric (volume in kg), Monday-first, always 7 entries. */
  volumes: readonly number[];
  /** Monday-first index of today (0–6). */
  todayIndex: number;
}

export function WeeklyChart({ volumes, todayIndex }: WeeklyChartProps) {
  const max = Math.max(...volumes, 1);

  return (
    <section className="bg-card rounded-card border border-border p-5">
      <p className="text-sm text-muted mb-4">Esta semana</p>
      <div className="flex items-end justify-between gap-2 h-24">
        {DAY_LETTERS.map((letter, i) => {
          const heightPct = volumes[i] > 0 ? Math.max((volumes[i] / max) * 100, 8) : 4;
          return (
            <div key={letter} className="flex flex-col items-center gap-1.5 flex-1 h-full justify-end">
              <div
                className={`w-full max-w-[14px] rounded-full ${
                  i === todayIndex ? 'bg-accent' : 'bg-muted'
                }`}
                style={{ height: `${heightPct}%` }}
              />
              <span className={`text-[10px] ${i === todayIndex ? 'text-accent' : 'text-muted'}`}>
                {letter}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
