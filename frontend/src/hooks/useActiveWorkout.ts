import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { WorkoutResponse } from '../types/api';

interface ActiveWorkoutResult {
  activeWorkout: WorkoutResponse | undefined;
  isLoading: boolean;
  isError: boolean;
}

/**
 * Fetches the active workout directly using a high-limit query so it is found
 * regardless of how many routines the user has. The backend allows up to 100
 * items per request; since only one workout can be active at a time, this is
 * always sufficient without needing multi-page traversal.
 */
export function useActiveWorkout(): ActiveWorkoutResult {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['workouts', 'active'],
    queryFn: () => apiFetch<WorkoutResponse[]>('/workouts?limit=100&offset=0'),
    select: (workouts) => workouts.find((w) => w.is_active),
  });
  return { activeWorkout: data, isLoading, isError };
}
