import { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { useAddCardio, useDeleteCardio } from '../../hooks/useSessions';
import { formatCardioEntry } from '../../lib/cardio';
import type { CardioEntryResponse } from '../../types/api';
import { CardioSheet } from './CardioSheet';

interface SessionCardioSectionProps {
  sessionId: string;
  entries: CardioEntryResponse[];
}

/** Treadmill cardio of a session: list, add on the fly, delete. */
export function SessionCardioSection({ sessionId, entries }: SessionCardioSectionProps) {
  const addCardio = useAddCardio();
  const deleteCardio = useDeleteCardio();
  const [sheetOpen, setSheetOpen] = useState(false);

  function closeSheet() {
    addCardio.reset();
    setSheetOpen(false);
  }

  return (
    <section
      aria-label="Cardio en cinta"
      style={{
        background: '#111511',
        borderRadius: '20px',
        border: '1px solid rgba(255,255,255,0.07)',
        padding: '16px',
        marginBottom: '24px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px' }}>
        <div style={{ minWidth: 0 }}>
          <h3
            style={{
              fontSize: '17px',
              fontWeight: 700,
              color: 'var(--text)',
              fontFamily: "'Barlow Semi Condensed', sans-serif",
              margin: 0,
            }}
          >
            Cardio
          </h3>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Cinta</span>
        </div>
        <button
          type="button"
          onClick={() => {
            addCardio.reset();
            setSheetOpen(true);
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            height: '34px',
            padding: '0 12px',
            borderRadius: '12px',
            background: 'rgba(43,229,129,0.10)',
            border: '1px solid rgba(43,229,129,0.3)',
            color: '#2BE581',
            fontSize: '13px',
            fontWeight: 700,
            cursor: 'pointer',
            flexShrink: 0,
          }}
        >
          <Plus size={15} />
          Añadir cardio
        </button>
      </div>

      {entries.length > 0 && (
        <ul aria-label="Cardio registrado" style={{ listStyle: 'none', margin: '12px 0 0', padding: 0 }}>
          {entries.map((entry) => {
            const summary = formatCardioEntry(entry);
            return (
              <li
                key={entry.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 0',
                  borderTop: '1px solid rgba(255,255,255,0.06)',
                }}
              >
                <span style={{ flex: 1, minWidth: 0, fontSize: '14px', color: 'var(--text)', fontWeight: 500 }}>
                  {summary}
                </span>
                <button
                  type="button"
                  aria-label={`Borrar cardio ${summary}`}
                  disabled={deleteCardio.isPending}
                  onClick={() => deleteCardio.mutate({ sessionId, entryId: entry.id })}
                  className="bg-transparent border-none cursor-pointer text-muted p-1"
                >
                  <Trash2 size={15} />
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {deleteCardio.isError && (
        <p className="text-xs text-danger" style={{ marginTop: '8px' }}>
          No se pudo borrar el cardio. Inténtalo de nuevo.
        </p>
      )}

      {sheetOpen && (
        <CardioSheet
          isPending={addCardio.isPending}
          errorMessage={addCardio.isError ? 'No se pudo guardar el cardio. Inténtalo de nuevo.' : null}
          onSave={(values) => addCardio.mutate({ sessionId, values }, { onSuccess: closeSheet })}
          onClose={closeSheet}
        />
      )}
    </section>
  );
}
