import { GUIDE_ID_BY_EXERCISE } from './catalogMapping';
import { GUIDES, getExerciseGuide } from './index';

// Keys only: the photos are never loaded here.
const photoFiles = new Set(
  Object.keys(import.meta.glob('/public/exercise-guides/*/*.webp')).map((p) => p.replace('/public/', '/')),
);

describe('exercise guides', () => {
  it('links every mapped catalog exercise to an existing guide', () => {
    const missing = Object.entries(GUIDE_ID_BY_EXERCISE).filter(([, id]) => GUIDES[id] === undefined);
    expect(missing).toEqual([]);
  });

  it('uses every guide for some catalog exercise', () => {
    const used = new Set(Object.values(GUIDE_ID_BY_EXERCISE));
    expect(Object.keys(GUIDES).filter((id) => !used.has(id))).toEqual([]);
  });

  it.each(Object.keys(GUIDES))('%s has both photos', (id) => {
    expect(photoFiles.has(`/exercise-guides/${id}/0.webp`)).toBe(true);
    expect(photoFiles.has(`/exercise-guides/${id}/1.webp`)).toBe(true);
  });

  it.each(Object.keys(GUIDES))('%s has 3 to 6 short Spanish steps', (id) => {
    const { steps } = GUIDES[id];
    expect(steps.length).toBeGreaterThanOrEqual(3);
    expect(steps.length).toBeLessThanOrEqual(6);
    for (const step of steps) {
      expect(step).toBe(step.trim());
      expect(step).toMatch(/^[A-ZÁÉÍÓÚÑ¿¡].*\.$/);
      expect(step.length).toBeLessThanOrEqual(180);
    }
  });

  it.each(Object.keys(GUIDES))('%s has a primary muscle', (id) => {
    expect(GUIDES[id].primaryMuscles.length).toBeGreaterThan(0);
  });

  it('resolves both machine variants to the same guide and photos', () => {
    const plate = getExerciseGuide('leg-press-plate-loaded');
    expect(plate?.id).toBe('Leg_Press');
    expect(plate?.photos).toEqual(['/exercise-guides/Leg_Press/0.webp', '/exercise-guides/Leg_Press/1.webp']);
    expect(getExerciseGuide('leg-press-selectorized')?.id).toBe('Leg_Press');
  });

  it('has no guide for an exercise without a fitting entry or an unknown id', () => {
    expect(getExerciseGuide('dragon-flag')).toBeNull();
    // Entries without source instructions, or a different variant, are left out.
    expect(getExerciseGuide('push-press')).toBeNull();
    expect(getExerciseGuide('side-plank')).toBeNull();
    expect(getExerciseGuide('cable-lateral-raise')).toBeNull();
    expect(getExerciseGuide('glute-kickback-machine-plate-loaded')).toBeNull();
    expect(getExerciseGuide('not-in-catalog')).toBeNull();
  });
});
