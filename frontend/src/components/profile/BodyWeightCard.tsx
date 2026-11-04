import { useState } from 'react';
import { Scale, Trash2 } from 'lucide-react';
import { Spinner } from '../Spinner';
import {
  useBodyWeightHistory,
  useDeleteBodyWeight,
  useRecordBodyWeight,
} from '../../hooks/useBodyWeight';

const MAX_WEIGHT_KG = 400;
const VISIBLE_ENTRIES = 7;

/** Local calendar day as YYYY-MM-DD (not UTC: a 00:30 weigh-in is today). */
function todayIso(): string {
  const d = new Date();
  return [
    d.getFullYear(),
    String(d.getMonth() + 1).padStart(2, '0'),
    String(d.getDate()).padStart(2, '0'),
  ].join('-');
}

function formatDay(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('es-ES', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function formatKg(value: number, signed = false): string {
  const number = value.toLocaleString('es-ES', {
    maximumFractionDigits: 1,
    signDisplay: signed ? 'exceptZero' : 'auto',
  });
  return `${number} kg`;
}

/** Accepts "84,5" and "84.5"; null when not a valid weight. */
function parseWeight(raw: string): number | null {
  const value = Number(raw.trim().replace(',', '.'));
  if (raw.trim() === '' || !Number.isFinite(value) || value <= 0 || value > MAX_WEIGHT_KG) {
    return null;
  }
  return value;
}

const fieldStyle = {
  height: '40px',
  padding: '0 12px',
  borderRadius: '12px',
  background: '#0f130f',
  border: '1px solid rgba(255,255,255,0.08)',
  color: 'var(--text)',
  fontSize: '15px',
  width: '100%',
} as const;

/** Body weight log: record a day's weight and browse the history. */
export function BodyWeightCard() {
  const { data, isLoading, isError } = useBodyWeightHistory();
  const recordWeight = useRecordBodyWeight();
  const deleteWeight = useDeleteBodyWeight();

  const [measuredOn, setMeasuredOn] = useState(todayIso);
  const [weightInput, setWeightInput] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  const history = data ?? [];
  const latest = history[0];
  const sameDayEntry = history.find((e) => e.measured_on === measuredOn);
  const visible = showAll ? history : history.slice(0, VISIBLE_ENTRIES);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const weightKg = parseWeight(weightInput);
    if (weightKg === null) {
      setFormError(`Introduce un peso mayor que 0 y de hasta ${MAX_WEIGHT_KG} kg.`);
      return;
    }
    setFormError(null);
    recordWeight.mutate(
      { measuredOn, weightKg },
      {
        onSuccess: () => {
          setWeightInput('');
          setMeasuredOn(todayIso());
        },
      },
    );
  }

  return (
    <section
      aria-labelledby="body-weight-title"
      style={{
        borderRadius: '20px',
        background: 'rgb(15,19,15)',
        border: '1px solid rgba(255,255,255,0.06)',
        padding: '16px',
        marginBottom: '16px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
        <Scale size={18} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
        <h2
          id="body-weight-title"
          style={{ flex: 1, margin: 0, fontSize: '15px', fontWeight: 600, color: 'var(--text)' }}
        >
          Peso corporal
        </h2>
        {latest && (
          <span
            aria-label="Último peso"
            style={{
              fontSize: '20px',
              fontWeight: 700,
              color: 'var(--text)',
              fontFamily: "'Barlow Semi Condensed', sans-serif",
            }}
          >
            {formatKg(latest.weight_kg)}
          </span>
        )}
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
          <label style={{ flex: 1.5, minWidth: 0, fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>
            Fecha
            <input
              type="date"
              value={measuredOn}
              max={todayIso()}
              onChange={(e) => setMeasuredOn(e.target.value || todayIso())}
              style={{ ...fieldStyle, marginTop: '4px', padding: '0 8px', colorScheme: 'dark' }}
            />
          </label>
          <label style={{ flex: 1, minWidth: 0, fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>
            Peso (kg)
            <input
              type="text"
              inputMode="decimal"
              placeholder={latest ? String(latest.weight_kg).replace('.', ',') : '80,0'}
              value={weightInput}
              onChange={(e) => setWeightInput(e.target.value)}
              style={{ ...fieldStyle, marginTop: '4px' }}
            />
          </label>
          <button
            type="submit"
            aria-label="Guardar peso"
            disabled={recordWeight.isPending}
            style={{
              height: '40px',
              padding: '0 14px',
              borderRadius: '12px',
              border: 'none',
              background: 'linear-gradient(135deg,#2BE581,#1fbd6a)',
              color: 'rgb(6,33,15)',
              fontWeight: 700,
              fontSize: '14px',
              cursor: recordWeight.isPending ? 'not-allowed' : 'pointer',
              opacity: recordWeight.isPending ? 0.6 : 1,
              flexShrink: 0,
            }}
          >
            Guardar
          </button>
        </div>
        {sameDayEntry && (
          <p className="text-xs text-muted" style={{ marginTop: '6px' }}>
            Ese día ya tiene {formatKg(sameDayEntry.weight_kg)}; se sustituirá.
          </p>
        )}
        {formError && (
          <p className="text-xs text-danger" style={{ marginTop: '6px' }}>
            {formError}
          </p>
        )}
        {recordWeight.isError && (
          <p className="text-xs text-danger" style={{ marginTop: '6px' }}>
            No se pudo guardar el peso. Inténtalo de nuevo.
          </p>
        )}
      </form>

      <div style={{ marginTop: '14px' }}>
        {isLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '12px 0' }}>
            <Spinner />
          </div>
        ) : isError ? (
          <p className="text-sm text-danger">No se pudo cargar el histórico de peso.</p>
        ) : history.length === 0 ? (
          <p className="text-sm text-muted">Aún no has registrado tu peso.</p>
        ) : (
          <>
            <ul aria-label="Histórico de peso" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {visible.map((entry, i) => {
                // History is newest first: the previous weigh-in is the next item.
                const previous = history[i + 1];
                const day = formatDay(entry.measured_on);
                return (
                  <li
                    key={entry.measured_on}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '10px 0',
                      borderTop: '1px solid rgba(255,255,255,0.05)',
                    }}
                  >
                    <span style={{ flex: 1, fontSize: '14px', color: 'var(--text-muted)' }}>{day}</span>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', minWidth: '60px', textAlign: 'right' }}>
                      {previous ? formatKg(entry.weight_kg - previous.weight_kg, true) : ''}
                    </span>
                    <span style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text)', minWidth: '64px', textAlign: 'right' }}>
                      {formatKg(entry.weight_kg)}
                    </span>
                    <button
                      type="button"
                      aria-label={`Borrar el peso del ${day}`}
                      disabled={deleteWeight.isPending}
                      onClick={() => deleteWeight.mutate(entry.measured_on)}
                      className="bg-transparent border-none cursor-pointer text-muted p-1"
                    >
                      <Trash2 size={15} />
                    </button>
                  </li>
                );
              })}
            </ul>
            {history.length > VISIBLE_ENTRIES && (
              <button
                type="button"
                onClick={() => setShowAll((v) => !v)}
                className="text-xs text-muted bg-transparent border-none cursor-pointer p-0"
                style={{ marginTop: '8px' }}
              >
                {showAll ? 'Ver menos' : `Ver todo (${history.length})`}
              </button>
            )}
            {deleteWeight.isError && (
              <p className="text-xs text-danger" style={{ marginTop: '6px' }}>
                No se pudo borrar el registro. Inténtalo de nuevo.
              </p>
            )}
          </>
        )}
      </div>
    </section>
  );
}
