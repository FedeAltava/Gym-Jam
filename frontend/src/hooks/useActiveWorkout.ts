import { useWorkouts } from './useWorkouts';
import type { WorkoutResponse } from '../types/api';

interface ActiveWorkoutResult {
  activeWorkout: WorkoutResponse | undefined;
  isLoading: boolean;
  isError: boolean;
}

/** Derives the active workout from the paginated workouts list. */
export function useActiveWorkout(): ActiveWorkoutResult {
  const { data, isLoading, isError } = useWorkouts();
  const activeWorkout = data?.pages.flat().find((w) => w.is_active);
  return { activeWorkout, isLoading, isError };
}
