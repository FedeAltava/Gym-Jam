import { EMPTY_CARDIO_FORM, formatCardioEntry, parseCardioForm } from './cardio';

const entry = {
  id: 'c1',
  duration_minutes: null,
  distance_km: null,
  speed_kmh: null,
  incline_percent: null,
  calories: null,
};

describe('parseCardioForm', () => {
  it('parses every field, accepting a decimal comma', () => {
    expect(
      parseCardioForm({
        durationMinutes: '20',
        distanceKm: '2,5',
        speedKmh: ' 7.5 ',
        inclinePercent: '3,5',
        calories: '250',
      }),
    ).toEqual({
      values: { durationMinutes: 20, distanceKm: 2.5, speedKmh: 7.5, inclinePercent: 3.5, calories: 250 },
    });
  });

  it('leaves empty fields as null', () => {
    expect(parseCardioForm({ ...EMPTY_CARDIO_FORM, calories: '180' })).toEqual({
      values: { durationMinutes: null, distanceKm: null, speedKmh: null, inclinePercent: null, calories: 180 },
    });
  });

  it('requires at least one value', () => {
    expect(parseCardioForm(EMPTY_CARDIO_FORM)).toEqual({ error: 'Rellena al menos un campo.' });
    expect(parseCardioForm({ ...EMPTY_CARDIO_FORM, speedKmh: '   ' })).toEqual({
      error: 'Rellena al menos un campo.',
    });
  });

  it.each([
    [{ durationMinutes: '0' }, 'Los minutos deben ser un número entero entre 1 y 1440.'],
    [{ durationMinutes: '20,5' }, 'Los minutos deben ser un número entero entre 1 y 1440.'],
    [{ durationMinutes: '1441' }, 'Los minutos deben ser un número entero entre 1 y 1440.'],
    [{ distanceKm: '0' }, 'La distancia debe ser mayor que 0.'],
    [{ distanceKm: 'abc' }, 'La distancia debe ser mayor que 0.'],
    [{ speedKmh: '-6' }, 'La velocidad debe ser mayor que 0.'],
    [{ inclinePercent: '-1' }, 'La pendiente debe estar entre 0 y 40 %.'],
    [{ inclinePercent: '40,5' }, 'La pendiente debe estar entre 0 y 40 %.'],
    [{ calories: '0' }, 'Las calorías deben ser un número entero entre 1 y 20000.'],
    [{ calories: '20001' }, 'Las calorías deben ser un número entero entre 1 y 20000.'],
  ])('rejects %o', (fields, error) => {
    expect(parseCardioForm({ ...EMPTY_CARDIO_FORM, ...fields })).toEqual({ error });
  });

  it('accepts an incline of 0 and 40', () => {
    expect(parseCardioForm({ ...EMPTY_CARDIO_FORM, inclinePercent: '0' })).toEqual({
      values: { durationMinutes: null, distanceKm: null, speedKmh: null, inclinePercent: 0, calories: null },
    });
    expect(parseCardioForm({ ...EMPTY_CARDIO_FORM, inclinePercent: '40' })).toMatchObject({
      values: { inclinePercent: 40 },
    });
  });
});

describe('formatCardioEntry', () => {
  it('joins the recorded values with Spanish number formatting', () => {
    expect(
      formatCardioEntry({
        ...entry,
        duration_minutes: 20,
        distance_km: 2.5,
        speed_kmh: 7.5,
        incline_percent: 3.5,
        calories: 250,
      }),
    ).toBe('20 min · 2,5 km · 7,5 km/h · pendiente 3,5 % · 250 kcal');
  });

  it('skips the values that were not recorded', () => {
    expect(formatCardioEntry({ ...entry, distance_km: 3.25, incline_percent: 0 })).toBe('3,25 km · pendiente 0 %');
  });
});
