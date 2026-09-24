/**
 * Placeholder with the same shape as a menu card, shown at the top of the
 * list while an uploaded PDF is being processed.
 */
export function MenuCardSkeleton() {
  return (
    <article
      role="status"
      aria-label="Leyendo tu PDF"
      style={{
        background: '#14160F',
        border: '1px solid #22251E',
        borderRadius: '16px',
        padding: '18px 20px',
        marginBottom: '12px',
      }}
    >
      <div className="animate-pulse" aria-hidden="true">
        <div
          style={{
            height: '17px',
            width: '60%',
            borderRadius: '6px',
            background: '#22251E',
            marginBottom: '10px',
          }}
        />
        <div
          style={{ height: '13px', width: '35%', borderRadius: '6px', background: '#22251E' }}
        />
      </div>
      <p style={{ fontSize: '12px', color: '#8B928A', margin: '12px 0 0' }}>Leyendo tu PDF...</p>
    </article>
  );
}
