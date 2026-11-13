import { X } from 'lucide-react';
import { LEVEL_LABELS, MUSCLE_LABELS, type ResolvedExerciseGuide } from '../../data/exerciseGuides';

interface ExerciseHowToSheetProps {
  exerciseName: string;
  guide: ResolvedExerciseGuide;
  onClose: () => void;
}

const PHOTOS = [
  { alt: 'Posición inicial', caption: '1 · Inicio' },
  { alt: 'Posición final', caption: '2 · Final' },
] as const;

const chipStyle = (primary: boolean) => ({
  padding: '4px 10px',
  borderRadius: '20px',
  fontSize: '12px',
  fontWeight: primary ? 700 : 600,
  background: primary ? 'rgba(43,229,129,0.12)' : 'rgba(255,255,255,0.05)',
  border: primary ? '1px solid rgba(43,229,129,0.35)' : '1px solid rgba(255,255,255,0.08)',
  color: primary ? 'var(--neon-green)' : 'var(--text-muted)',
});

/** Photos, muscles and steps of an exercise (Free Exercise DB). */
export function ExerciseHowToSheet({ exerciseName, guide, onClose }: ExerciseHowToSheetProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/60"
      role="dialog"
      aria-modal="true"
      aria-label={`Cómo se hace: ${exerciseName}`}
      onClick={onClose}
    >
      <div
        className="w-full md:max-w-md flex flex-col"
        style={{
          maxHeight: '88vh',
          background: '#111511',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: '20px 20px 0 0',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 px-4 pt-4 pb-3 shrink-0">
          <div className="min-w-0">
            <p
              style={{
                margin: 0,
                fontSize: '12px',
                fontWeight: 700,
                color: 'var(--neon-green)',
                textTransform: 'uppercase',
                letterSpacing: '1px',
              }}
            >
              Cómo se hace
            </p>
            <h2
              style={{
                margin: '2px 0 0',
                fontSize: '20px',
                fontWeight: 700,
                color: 'var(--text)',
                fontFamily: "'Barlow Semi Condensed', sans-serif",
              }}
            >
              {exerciseName}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="bg-transparent border-none cursor-pointer text-muted p-1"
          >
            <X size={20} />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 min-h-0 px-4 pb-4" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '10px' }}>
            {PHOTOS.map(({ alt, caption }, index) => (
              <figure key={caption} style={{ margin: 0, display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <img
                  src={guide.photos[index]}
                  alt={alt}
                  style={{
                    width: '100%',
                    aspectRatio: '3 / 2',
                    objectFit: 'cover',
                    borderRadius: '14px',
                    background: '#EAF0EA',
                    display: 'block',
                  }}
                />
                <figcaption
                  style={{
                    fontSize: '12px',
                    fontWeight: 700,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                  }}
                >
                  {caption}
                </figcaption>
              </figure>
            ))}
          </div>

          <ul
            aria-label="Músculos"
            style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexWrap: 'wrap', gap: '6px' }}
          >
            {guide.primaryMuscles.map((m) => (
              <li key={`p-${m}`} style={chipStyle(true)}>
                {MUSCLE_LABELS[m]}
              </li>
            ))}
            {guide.secondaryMuscles.map((m) => (
              <li key={`s-${m}`} style={chipStyle(false)}>
                {MUSCLE_LABELS[m]}
              </li>
            ))}
            <li style={chipStyle(false)}>{LEVEL_LABELS[guide.level]}</li>
          </ul>

          <ol
            aria-label="Pasos"
            style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '10px' }}
          >
            {guide.steps.map((step, index) => (
              <li key={step} style={{ display: 'flex', gap: '10px', fontSize: '14px', lineHeight: 1.4, color: 'var(--text)' }}>
                <span
                  aria-hidden="true"
                  style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '8px',
                    background: 'rgba(43,229,129,0.12)',
                    color: 'var(--neon-green)',
                    fontSize: '12px',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  {index + 1}
                </span>
                <span>{step}</span>
              </li>
            ))}
          </ol>

          <p style={{ margin: 0, fontSize: '11px', color: 'var(--text-muted)' }}>
            Fotos y pasos: Free Exercise DB (dominio público)
          </p>
          <button
            type="button"
            onClick={onClose}
            style={{
              width: '100%',
              height: '54px',
              border: 'none',
              borderRadius: '16px',
              background: 'linear-gradient(135deg,#2BE581,#1fbd6a)',
              color: 'rgb(6,33,15)',
              fontSize: '16px',
              fontWeight: 700,
              fontFamily: 'Barlow, sans-serif',
              cursor: 'pointer',
              flexShrink: 0,
            }}
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
}
