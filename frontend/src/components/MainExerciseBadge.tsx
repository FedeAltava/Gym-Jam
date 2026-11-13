// The main lift of a training day: the heaviest compound, done first while
// fresh. The app treats the first exercise of each day as the main one.
export function MainExerciseBadge() {
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 6px',
        borderRadius: '6px',
        background: 'rgba(43,229,129,0.12)',
        border: '1px solid rgba(43,229,129,0.35)',
        color: '#2BE581',
        fontSize: '10px',
        fontWeight: 700,
        letterSpacing: '0.6px',
        textTransform: 'uppercase',
        flexShrink: 0,
      }}
    >
      Principal
    </span>
  );
}
