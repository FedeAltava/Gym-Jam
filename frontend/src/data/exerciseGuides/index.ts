import { ARMS_GUIDES } from './arms';
import { BACK_GUIDES } from './back';
import { GUIDE_ID_BY_EXERCISE } from './catalogMapping';
import { CHEST_GUIDES } from './chest';
import { CORE_GUIDES } from './core';
import { LEGS_GUIDES } from './legs';
import { OWN_GUIDES, OWN_GUIDE_PHOTOS } from './own';
import { SHOULDERS_GUIDES } from './shoulders';
import type { ExerciseGuide, GuideLevel, GuideMuscle } from './types';

export type { ExerciseGuide, GuideLevel, GuideMuscle } from './types';
export { OWN_GUIDES, OWN_GUIDE_PHOTOS } from './own';

// How-to guides from Free Exercise DB (https://github.com/yuhonas/free-exercise-db,
// public domain). Photos are self-hosted under public/exercise-guides/<guide id>/.
export const FREE_EXERCISE_DB_GUIDES: Record<string, ExerciseGuide> = {
  ...ARMS_GUIDES,
  ...BACK_GUIDES,
  ...CHEST_GUIDES,
  ...CORE_GUIDES,
  ...LEGS_GUIDES,
  ...SHOULDERS_GUIDES,
};

export const GUIDES: Record<string, ExerciseGuide> = { ...FREE_EXERCISE_DB_GUIDES, ...OWN_GUIDES };

const FREE_EXERCISE_DB_CREDIT = 'Fotos y pasos: Free Exercise DB (dominio público)';

export interface ResolvedExerciseGuide extends ExerciseGuide {
  id: string;
  // Start and end position, or a single photo; empty when the guide has none yet.
  photos: string[];
  // CSS aspect ratio of the photos.
  photoAspect: string;
  // Attribution shown with the guide, if any, and the link it requires.
  credit: string | null;
  creditUrl: string | null;
}

function photoUrl(guideId: string, index: number): string {
  return `${import.meta.env.BASE_URL}exercise-guides/${guideId}/${index}.webp`;
}

/** The how-to guide of a catalog exercise, or null when it has none. */
export function getExerciseGuide(exerciseId: string): ResolvedExerciseGuide | null {
  const id = GUIDE_ID_BY_EXERCISE[exerciseId];
  const guide = id === undefined ? undefined : GUIDES[id];
  if (id === undefined || guide === undefined) return null;
  if (FREE_EXERCISE_DB_GUIDES[id] !== undefined) {
    return {
      ...guide,
      id,
      photos: [photoUrl(id, 0), photoUrl(id, 1)],
      photoAspect: '3 / 2',
      credit: FREE_EXERCISE_DB_CREDIT,
      creditUrl: null,
    };
  }
  const own = OWN_GUIDE_PHOTOS[id];
  if (own === undefined) return { ...guide, id, photos: [], photoAspect: '3 / 2', credit: null, creditUrl: null };
  return {
    ...guide,
    id,
    photos: Array.from({ length: own.count }, (_, n) => photoUrl(id, n)),
    photoAspect: own.aspectRatio,
    credit: own.credit,
    creditUrl: own.creditUrl,
  };
}

export const MUSCLE_LABELS: Record<GuideMuscle, string> = {
  abdominals: 'Abdominales',
  abductors: 'Abductores',
  adductors: 'Aductores',
  biceps: 'Bíceps',
  calves: 'Gemelos',
  chest: 'Pecho',
  forearms: 'Antebrazos',
  glutes: 'Glúteos',
  hamstrings: 'Isquios',
  lats: 'Dorsales',
  'lower back': 'Lumbares',
  'middle back': 'Espalda media',
  neck: 'Cuello',
  quadriceps: 'Cuádriceps',
  shoulders: 'Hombros',
  traps: 'Trapecios',
  triceps: 'Tríceps',
};

export const LEVEL_LABELS: Record<GuideLevel, string> = {
  beginner: 'Principiante',
  intermediate: 'Intermedio',
  expert: 'Avanzado',
};
