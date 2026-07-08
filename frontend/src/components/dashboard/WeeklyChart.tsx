const DAY_LETTERS = ['L', 'M', 'X', 'J', 'V', 'S', 'D'] as const;

interface WeeklyChartProps {
  /** Per-day activity metric (volume in kg), Monday-first, always 7 entries. */
  volumes: readonly number[];
  /** Monday-first index of today (0–6). */
  todayIndex: number;
  /** Number of sessions completed this week. */
  sessionsThisWeek: number;
  /** Number of plan days in the active workout. */
  planDaysCount: number;
}

export function WeeklyChart({ volumes, todayIndex, sessionsThisWeek, planDaysCount }: WeeklyChartProps) {
  const max = Math.max(...volumes, 1);

  return (
    <section
      style={{
        borderRadius: '22px',
        padding: '20px',
        background: '#111511',
        border: '1px solid rgba(255,255,255,0.07)',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px',
        }}
      >
        <span style={{ fontSize: '15px', fontWeight: 700, color: '#EAF0EA' }}>Esta semana</span>
        <span style={{ fontSize: '13px', color: '#7E8A7E', fontWeight: 600 }}>
          {sessionsThisWeek} de {planDaysCount} sesiones
        </span>
      </div>

      {/* Bars */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'space-between',
          height: '90px',
          gap: '8px',
        }}
      >
        {DAY_LETTERS.map((letter, i) => {
          const isToday = i === todayIndex;
          const heightPct = volumes[i] > 0 ? Math.max((volumes[i] / max) * 100, 8) : 20;

          let barBackground: string;
          if (isToday) {
            barBackground = 'linear-gradient(180deg,#C6F24E,#2BE581)';
          } else if (volumes[i] > 0) {
            barBackground = '#2BE581';
          } else {
            barBackground = 'rgba(255,255,255,0.12)';
          }

          return (
            <div
              key={letter}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '8px',
                height: '100%',
                justifyContent: 'flex-end',
              }}
            >
              <div
                style={{
                  width: '100%',
                  maxWidth: '26px',
                  height: `${heightPct}%`,
                  borderRadius: '7px',
                  background: barBackground,
                  ...(isToday ? { boxShadow: '0 0 14px rgba(43,229,129,0.5)' } : {}),
                }}
              />
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: isToday ? 700 : 600,
                  color: isToday ? '#C6F24E' : '#7E8A7E',
                }}
              >
                {letter}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
