// Values as published by Free Exercise DB.
export type GuideLevel = 'beginner' | 'intermediate' | 'expert';

export type GuideMuscle =
  | 'abdominals'
  | 'abductors'
  | 'adductors'
  | 'biceps'
  | 'calves'
  | 'chest'
  | 'forearms'
  | 'glutes'
  | 'hamstrings'
  | 'lats'
  | 'lower back'
  | 'middle back'
  | 'neck'
  | 'quadriceps'
  | 'shoulders'
  | 'traps'
  | 'triceps';

export interface ExerciseGuide {
  level: GuideLevel;
  primaryMuscles: GuideMuscle[];
  secondaryMuscles: GuideMuscle[];
  // Spanish, one instruction per step.
  steps: string[];
}
