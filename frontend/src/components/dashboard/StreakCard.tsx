interface StreakCardProps {
  streak: number;
  /** Monday-first weekday indexes (0–6) that belong to the active plan. */
  planDays: ReadonlySet<number>;
  /** Monday-first weekday indexes with a completed session this week. */
  completedDays: ReadonlySet<number>;
}

function segmentColor(index: number, planDays: ReadonlySet<number>, completedDays: ReadonlySet<number>): string {
  if (planDays.has(index) && completedDays.has(index)) return '#2BE581';
  return 'rgba(255,255,255,0.12)';
}

export function StreakCard({ streak, planDays, completedDays }: StreakCardProps) {
  return (
    <section
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
        {/* Label row */}
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
          >
            <path d="M12 2s4 4 4 8a4 4 0 1 1-8 0c0-1 .5-2 .5-2S6 12 6 15a6 6 0 1 0 12 0c0-5-6-13-6-13z" />
          </svg>
          Racha activa
        </div>

        {/* Number row */}
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

        {/* Segments */}
        <div style={{ display: 'flex', gap: '5px', marginTop: '14px' }} aria-hidden="true">
          {Array.from({ length: 7 }, (_, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                height: '6px',
                borderRadius: '3px',
                background: segmentColor(i, planDays, completedDays),
              }}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
