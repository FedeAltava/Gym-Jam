export interface MuscleSets {
  muscle: string;
  /** Sets logged this week. */
  done: number;
  /** Sets the active routine plans per week. */
  planned: number;
}

interface MuscleSetsCardProps {
  rows: readonly MuscleSets[];
}

/** This week's sets per muscle group against the routine's weekly plan. */
export function MuscleSetsCard({ rows }: MuscleSetsCardProps) {
  return (
    <section
      aria-label="Series por músculo"
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
        }}
      >
        <span style={{ fontSize: '15px', fontWeight: 700, color: '#EAF0EA' }}>Series por músculo</span>
        <span style={{ fontSize: '13px', color: '#7E8A7E', fontWeight: 600 }}>esta semana</span>
      </div>

      {rows.length === 0 ? (
        <p style={{ fontSize: '13px', color: '#7E8A7E', margin: 0 }}>Aún no hay series esta semana.</p>
      ) : (
        <ul aria-label="Series por músculo" style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: '12px' }}>
          {rows.map(({ muscle, done, planned }) => {
            const complete = planned > 0 && done >= planned;
            const fillPct = planned > 0 ? Math.min(done / planned, 1) * 100 : 100;
            return (
              <li
                key={muscle}
                aria-label={`${muscle}: ${done} de ${planned} series`}
                style={{ display: 'flex', alignItems: 'center', gap: '12px' }}
              >
                <span style={{ width: '64px', flexShrink: 0, fontSize: '13px', fontWeight: 600, color: '#EAF0EA' }}>
                  {muscle}
                </span>
                <div
                  aria-hidden="true"
                  style={{ flex: 1, height: '8px', borderRadius: '4px', background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}
                >
                  <div
                    style={{
                      width: `${fillPct}%`,
                      height: '100%',
                      borderRadius: '4px',
                      background: complete
                        ? '#2BE581'
                        : planned > 0
                          ? 'linear-gradient(90deg,#2BE581,#C6F24E)'
                          : 'rgba(255,255,255,0.25)',
                      transition: 'width 0.3s',
                    }}
                  />
                </div>
                <span
                  aria-hidden="true"
                  style={{
                    width: '40px',
                    flexShrink: 0,
                    textAlign: 'right',
                    fontSize: '12px',
                    fontWeight: 700,
                    fontVariantNumeric: 'tabular-nums',
                    color: complete ? '#2BE581' : '#7E8A7E',
                  }}
                >
                  {planned > 0 ? `${done}/${planned}` : done}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
