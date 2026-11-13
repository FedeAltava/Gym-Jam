import { GUIDE_ID_BY_EXERCISE } from './catalogMapping';
import { FREE_EXERCISE_DB_GUIDES, GUIDES, OWN_GUIDES, getExerciseGuide } from './index';

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

  it.each(Object.keys(FREE_EXERCISE_DB_GUIDES))('%s has both photos', (id) => {
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
    expect(plate?.credit).toBe('Fotos y pasos: Free Exercise DB (dominio público)');
    expect(getExerciseGuide('leg-press-selectorized')?.id).toBe('Leg_Press');
  });

  // No usable Free Exercise DB entry: steps researched and written by us, no photos.
  it.each([
    'dragon-flag',
    'toe-to-bar',
    'landmine-press',
    'lateral-raise-machine-plate-loaded',
    'lateral-raise-machine-selectorized',
    'glute-kickback-machine-plate-loaded',
    'glute-kickback-machine-selectorized',
    'push-press',
    'side-plank',
    'cable-lateral-raise',
  ])('%s has our own guide, without photos', (exerciseId) => {
    const guide = getExerciseGuide(exerciseId);
    expect(guide).not.toBeNull();
    expect(OWN_GUIDES[guide!.id]).toBeDefined();
    expect(guide!.photos).toEqual([]);
    expect(guide!.credit).toBeNull();
  });

  it('resolves both machine variants of our own guide to the same guide', () => {
    expect(getExerciseGuide('lateral-raise-machine-plate-loaded')?.id).toBe(
      getExerciseGuide('lateral-raise-machine-selectorized')?.id,
    );
    expect(getExerciseGuide('glute-kickback-machine-plate-loaded')?.id).toBe(
      getExerciseGuide('glute-kickback-machine-selectorized')?.id,
    );
  });

  it.each(Object.keys(OWN_GUIDES))('%s ships no photo files', (id) => {
    expect(FREE_EXERCISE_DB_GUIDES[id]).toBeUndefined();
    expect(photoFiles.has(`/exercise-guides/${id}/0.webp`)).toBe(false);
  });

  it('has no guide for an exercise outside the catalog', () => {
    expect(getExerciseGuide('not-in-catalog')).toBeNull();
  });
});
