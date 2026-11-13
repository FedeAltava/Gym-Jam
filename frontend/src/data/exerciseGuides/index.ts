import { ARMS_GUIDES } from './arms';
import { BACK_GUIDES } from './back';
import { GUIDE_ID_BY_EXERCISE } from './catalogMapping';
import { CHEST_GUIDES } from './chest';
import { CORE_GUIDES } from './core';
import { LEGS_GUIDES } from './legs';
import { SHOULDERS_GUIDES } from './shoulders';
import type { ExerciseGuide, GuideLevel, GuideMuscle } from './types';

export type { ExerciseGuide, GuideLevel, GuideMuscle } from './types';

// How-to guides from Free Exercise DB (https://github.com/yuhonas/free-exercise-db,
// public domain). Photos are self-hosted under public/exercise-guides/<guide id>/.
export const GUIDES: Record<string, ExerciseGuide> = {
  ...ARMS_GUIDES,
  ...BACK_GUIDES,
  ...CHEST_GUIDES,
  ...CORE_GUIDES,
  ...LEGS_GUIDES,
  ...SHOULDERS_GUIDES,
};

export interface ResolvedExerciseGuide extends ExerciseGuide {
  id: string;
  // Start and end position.
  photos: [string, string];
}

function photoUrl(guideId: string, index: 0 | 1): string {
  return `${import.meta.env.BASE_URL}exercise-guides/${guideId}/${index}.webp`;
}

/** The how-to guide of a catalog exercise, or null when it has none. */
export function getExerciseGuide(exerciseId: string): ResolvedExerciseGuide | null {
  const id = GUIDE_ID_BY_EXERCISE[exerciseId];
  const guide = id === undefined ? undefined : GUIDES[id];
  if (id === undefined || guide === undefined) return null;
  return { ...guide, id, photos: [photoUrl(id, 0), photoUrl(id, 1)] };
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
