import { useState, type FormEvent } from 'react';
import { X } from 'lucide-react';
import { EMPTY_CARDIO_FORM, parseCardioForm, type CardioForm, type CardioValues } from '../../lib/cardio';

interface CardioSheetProps {
  isPending: boolean;
  // Error from the server; validation errors are handled here.
  errorMessage: string | null;
  onSave: (values: CardioValues) => void;
  onClose: () => void;
}

const FIELDS: { key: keyof CardioForm; label: string; inputMode: 'numeric' | 'decimal' }[] = [
  { key: 'durationMinutes', label: 'Minutos', inputMode: 'numeric' },
  { key: 'distanceKm', label: 'Distancia (km)', inputMode: 'decimal' },
  { key: 'speedKmh', label: 'Velocidad (km/h)', inputMode: 'decimal' },
  { key: 'inclinePercent', label: 'Pendiente (%)', inputMode: 'decimal' },
  { key: 'calories', label: 'Calorías (kcal)', inputMode: 'numeric' },
];

const fieldStyle = {
  height: '40px',
  padding: '0 12px',
  borderRadius: '12px',
  background: '#0f130f',
  border: '1px solid rgba(255,255,255,0.08)',
  color: 'var(--text)',
  fontSize: '15px',
  width: '100%',
  marginTop: '4px',
} as const;

/** Record a treadmill cardio block: every value optional, at least one required. */
export function CardioSheet({ isPending, errorMessage, onSave, onClose }: CardioSheetProps) {
  const [form, setForm] = useState<CardioForm>(EMPTY_CARDIO_FORM);
  const [validationError, setValidationError] = useState<string | null>(null);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const parsed = parseCardioForm(form);
    if ('error' in parsed) {
      setValidationError(parsed.error);
      return;
    }
    setValidationError(null);
    onSave(parsed.values);
  }

  const error = validationError ?? errorMessage;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/60"
      role="dialog"
      aria-modal="true"
      aria-label="Añadir cardio"
      onClick={onClose}
    >
      <div
        className="w-full md:max-w-md flex flex-col"
        style={{
          maxHeight: '80vh',
          background: '#111511',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: '20px 20px 0 0',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-4 pt-4 pb-2 shrink-0">
          <div className="min-w-0">
            <h2 className="text-base font-bold text-text" style={{ margin: 0 }}>
              Añadir cardio
            </h2>
            <p className="text-xs text-muted">Cinta · rellena solo lo que quieras</p>
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

        <form
          onSubmit={handleSubmit}
          noValidate
          className="overflow-y-auto px-4"
          style={{ paddingBottom: 'calc(16px + env(safe-area-inset-bottom))' }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            {FIELDS.map((field) => (
              <label
                key={field.key}
                style={{ minWidth: 0, fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}
              >
                {field.label}
                <input
                  type="text"
                  inputMode={field.inputMode}
                  value={form[field.key]}
                  onChange={(e) => setForm((prev) => ({ ...prev, [field.key]: e.target.value }))}
                  style={fieldStyle}
                />
              </label>
            ))}
          </div>

          {error && <p className="text-sm text-danger" style={{ marginTop: '12px' }}>{error}</p>}

          <button
            type="submit"
            disabled={isPending}
            style={{
              width: '100%',
              height: '46px',
              marginTop: '14px',
              borderRadius: '14px',
              border: 'none',
              background: 'linear-gradient(135deg,#2BE581,#1fbd6a)',
              color: 'rgb(6,33,15)',
              fontWeight: 700,
              fontSize: '15px',
              cursor: isPending ? 'not-allowed' : 'pointer',
              opacity: isPending ? 0.6 : 1,
            }}
          >
            {isPending ? 'Guardando…' : 'Guardar'}
          </button>
        </form>
      </div>
    </div>
  );
}
