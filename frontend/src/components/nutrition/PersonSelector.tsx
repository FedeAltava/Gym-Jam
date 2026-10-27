import type { MenuVariant } from './groupMenus';

interface PersonSelectorProps {
  variants: MenuVariant[];
  selectedId: string;
  onSelect: (id: string) => void;
}

/** Segmented control to switch between the per-person variants of a menu. */
export function PersonSelector({ variants, selectedId, onSelect }: PersonSelectorProps) {
  return (
    <div
      role="group"
      aria-label="Persona"
      style={{
        display: 'flex',
        gap: '4px',
        padding: '4px',
        marginBottom: '16px',
        background: '#14160F',
        border: '1px solid #22251E',
        borderRadius: '14px',
      }}
    >
      {variants.map((variant, index) => {
        const active = variant.id === selectedId;
        return (
          <button
            key={variant.id}
            type="button"
            aria-pressed={active}
            onClick={() => onSelect(variant.id)}
            style={{
              flex: 1,
              padding: '10px 12px',
              border: 'none',
              borderRadius: '10px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 700,
              background: active ? '#2BE581' : 'transparent',
              color: active ? 'rgb(6,33,15)' : 'var(--text)',
            }}
          >
            {variant.person ?? `Opción ${index + 1}`}
          </button>
        );
      })}
    </div>
  );
}
