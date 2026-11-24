import type { CardioEntryResponse } from '../types/api';

// Treadmill cardio: every value is optional, at least one is required.
// Same limits as the backend (CardioEntry in the domain).
const MAX_DURATION_MINUTES = 1440;
const MAX_CALORIES = 20000;
const MAX_INCLINE_PERCENT = 40;

export interface CardioValues {
  durationMinutes: number | null;
  distanceKm: number | null;
  speedKmh: number | null;
  inclinePercent: number | null;
  calories: number | null;
}

export type CardioForm = Record<keyof CardioValues, string>;

export const EMPTY_CARDIO_FORM: CardioForm = {
  durationMinutes: '',
  distanceKm: '',
  speedKmh: '',
  inclinePercent: '',
  calories: '',
};

// Empty → null; otherwise the number typed, accepting a decimal comma.
// Unparseable text becomes NaN so the range checks reject it.
function toNumber(raw: string): number | null {
  const text = raw.trim().replace(',', '.');
  if (text === '') return null;
  return /^-?\d+(\.\d+)?$/.test(text) ? Number(text) : NaN;
}

function isPositive(value: number | null, max = Infinity): boolean {
  return value === null || (value > 0 && value <= max);
}

function isWholeInRange(value: number | null, max: number): boolean {
  return value === null || (Number.isInteger(value) && value >= 1 && value <= max);
}

/** Validate the sheet's inputs; returns the values to send or the first error. */
export function parseCardioForm(form: CardioForm): { values: CardioValues } | { error: string } {
  const values: CardioValues = {
    durationMinutes: toNumber(form.durationMinutes),
    distanceKm: toNumber(form.distanceKm),
    speedKmh: toNumber(form.speedKmh),
    inclinePercent: toNumber(form.inclinePercent),
    calories: toNumber(form.calories),
  };
  if (Object.values(values).every((value) => value === null)) {
    return { error: 'Rellena al menos un campo.' };
  }
  if (!isWholeInRange(values.durationMinutes, MAX_DURATION_MINUTES)) {
    return { error: `Los minutos deben ser un número entero entre 1 y ${MAX_DURATION_MINUTES}.` };
  }
  if (!isPositive(values.distanceKm)) return { error: 'La distancia debe ser mayor que 0.' };
  if (!isPositive(values.speedKmh)) return { error: 'La velocidad debe ser mayor que 0.' };
  const incline = values.inclinePercent;
  if (incline !== null && !(incline >= 0 && incline <= MAX_INCLINE_PERCENT)) {
    return { error: `La pendiente debe estar entre 0 y ${MAX_INCLINE_PERCENT} %.` };
  }
  if (!isWholeInRange(values.calories, MAX_CALORIES)) {
    return { error: `Las calorías deben ser un número entero entre 1 y ${MAX_CALORIES}.` };
  }
  return { values };
}

const numberFormat = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 });

/** One line per entry, e.g. "20 min · 2,5 km · 7,5 km/h · pendiente 3,5 % · 250 kcal". */
export function formatCardioEntry(entry: CardioEntryResponse): string {
  const parts: string[] = [];
  if (entry.duration_minutes !== null) parts.push(`${numberFormat.format(entry.duration_minutes)} min`);
  if (entry.distance_km !== null) parts.push(`${numberFormat.format(entry.distance_km)} km`);
  if (entry.speed_kmh !== null) parts.push(`${numberFormat.format(entry.speed_kmh)} km/h`);
  if (entry.incline_percent !== null) parts.push(`pendiente ${numberFormat.format(entry.incline_percent)} %`);
  if (entry.calories !== null) parts.push(`${numberFormat.format(entry.calories)} kcal`);
  return parts.join(' · ');
}
