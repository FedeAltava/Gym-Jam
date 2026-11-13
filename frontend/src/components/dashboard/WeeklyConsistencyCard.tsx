export interface WeekSessions {
  /** Monday 00:00 UTC of the week. */
  start: Date;
  sessions: number;
}

interface WeeklyConsistencyCardProps {
  /** Oldest first; the last one is the current week. */
  weeks: readonly WeekSessions[];
  /** Number of plan days in the active workout (0 when there is none). */
  planDaysCount: number;
}

function shortDate(date: Date): string {
  return `${date.getUTCDate()}/${date.getUTCMonth() + 1}`;
}

/** Sessions in each of the last weeks against the routine's plan days. */
export function WeeklyConsistencyCard({ weeks, planDaysCount }: WeeklyConsistencyCardProps) {
  const target = planDaysCount > 0 ? planDaysCount : Math.max(...weeks.map((w) => w.sessions), 1);
  const completeWeeks = weeks.filter((w) => planDaysCount > 0 && w.sessions >= planDaysCount).length;
  const currentIndex = weeks.length - 1;

  return (
    <section
      aria-label="Constancia por semanas"
      style={{
        borderRadius: '22px',
        padding: '20px',
        background: '#111511',
        border: '1px solid rgba(255,255,255,0.07)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px',
          gap: '12px',
        }}
      >
        <span style={{ fontSize: '15px', fontWeight: 700, color: '#EAF0EA' }}>Constancia</span>
        <span style={{ fontSize: '13px', color: '#7E8A7E', fontWeight: 600 }}>
          {completeWeeks} de {weeks.length} semanas completas
        </span>
      </div>

      <ol
        aria-label="Constancia por semanas"
        style={{
          listStyle: 'none',
          margin: 0,
          padding: 0,
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'space-between',
          height: '90px',
          gap: '8px',
        }}
      >
        {weeks.map((week, i) => {
          const isCurrent = i === currentIndex;
          const complete = planDaysCount > 0 && week.sessions >= planDaysCount;
          const heightPct = week.sessions > 0 ? Math.max(Math.min(week.sessions / target, 1) * 100, 12) : 20;
          const barBackground = complete
            ? isCurrent
              ? 'linear-gradient(180deg,#C6F24E,#2BE581)'
              : '#2BE581'
            : week.sessions > 0
              ? 'rgba(43,229,129,0.45)'
              : 'rgba(255,255,255,0.12)';
          return (
            <li
              key={week.start.toISOString()}
              aria-label={`Semana del ${shortDate(week.start)}: ${week.sessions} de ${planDaysCount} sesiones`}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '6px',
                height: '100%',
                justifyContent: 'flex-end',
              }}
            >
              <span
                aria-hidden="true"
                style={{ fontSize: '11px', fontWeight: 700, color: complete ? '#2BE581' : '#7E8A7E' }}
              >
                {week.sessions}
              </span>
              <div
                aria-hidden="true"
                style={{
                  width: '100%',
                  maxWidth: '26px',
                  height: `${heightPct}%`,
                  borderRadius: '7px',
                  background: barBackground,
                  ...(isCurrent && complete ? { boxShadow: '0 0 14px rgba(43,229,129,0.5)' } : {}),
                }}
              />
              <span
                aria-hidden="true"
                style={{
                  fontSize: '10px',
                  fontWeight: isCurrent ? 700 : 600,
                  color: isCurrent ? '#C6F24E' : '#7E8A7E',
                  whiteSpace: 'nowrap',
                }}
              >
                {shortDate(week.start)}
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
