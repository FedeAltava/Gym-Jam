const DAY_LETTERS = ['L', 'M', 'X', 'J', 'V', 'S', 'D'] as const;

interface WeeklyChartProps {
  /** Active streak from the stats endpoint. */
  streak: number;
  /** Per-day activity metric (volume in kg), Monday-first, always 7 entries. */
  volumes: readonly number[];
  /** Monday-first index of today (0–6). */
  todayIndex: number;
  /** Number of sessions completed this week. */
  sessionsThisWeek: number;
  /** Number of plan days in the active workout. */
  planDaysCount: number;
}

/** Home hero: the active streak over this week's volume per day. */
export function WeeklyChart({ streak, volumes, todayIndex, sessionsThisWeek, planDaysCount }: WeeklyChartProps) {
  const max = Math.max(...volumes, 1);

  return (
    <section
      aria-label="Esta semana"
      style={{
        position: 'relative',
        borderRadius: '24px',
        padding: '22px',
        overflow: 'hidden',
        background: 'linear-gradient(135deg,#123021 0%,#0c1a12 60%)',
        border: '1px solid rgba(43,229,129,0.25)',
      }}
    >
      {/* Glow orb */}
      <div
        style={{
          position: 'absolute',
          right: '-30px',
          top: '-30px',
          width: '140px',
          height: '140px',
          borderRadius: '50%',
          background: 'radial-gradient(circle,rgba(43,229,129,0.35),transparent 70%)',
          pointerEvents: 'none',
        }}
      />
      <div style={{ position: 'relative' }}>
        {/* Streak */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: '#2BE581',
            fontSize: '13px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '1.5px',
          }}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#2BE581"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M12 2s4 4 4 8a4 4 0 1 1-8 0c0-1 .5-2 .5-2S6 12 6 15a6 6 0 1 0 12 0c0-5-6-13-6-13z" />
          </svg>
          Racha activa
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '10px', marginTop: '6px' }}>
          <span
            style={{
              fontSize: '60px',
              lineHeight: 0.9,
              fontWeight: 800,
              color: '#EAF0EA',
              fontFamily: "'Barlow Semi Condensed', sans-serif",
            }}
          >
            {streak}
          </span>
          <span style={{ fontSize: '18px', color: '#9fb0a2', fontWeight: 600, paddingBottom: '8px' }}>
            días seguidos
          </span>
        </div>

        {/* Week header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginTop: '20px',
            marginBottom: '14px',
          }}
        >
          <span style={{ fontSize: '15px', fontWeight: 700, color: '#EAF0EA' }}>Esta semana</span>
          <span style={{ fontSize: '13px', color: '#9fb0a2', fontWeight: 600 }}>
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
      </div>
    </section>
  );
}
