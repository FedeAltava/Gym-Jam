import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { ExerciseResponse, WorkoutExerciseResponse } from '../types/api';

export function useExercises(muscleGroup?: string) {
  return useQuery({
    queryKey: ['exercises', muscleGroup ?? ''],
    queryFn: () => {
      const url = muscleGroup
        ? `/exercises?muscle_group=${encodeURIComponent(muscleGroup)}`
        : '/exercises';
      return apiFetch<ExerciseResponse[]>(url);
    },
    // The catalog is static — keep it fresh for a while to avoid refetches.
    staleTime: 1000 * 60 * 5,
  });
}

interface AddExercisePayload {
  day: string;
  exerciseId: string;
}

export function useAddExercise(workoutId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ day, exerciseId }: AddExercisePayload) =>
      apiFetch<WorkoutExerciseResponse>(
        `/workouts/${workoutId}/training-days/${day}/exercises`,
        {
          method: 'POST',
          body: JSON.stringify({ exercise_id: exerciseId }),
        },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workouts', workoutId] }),
  });
}

interface RemoveExercisePayload {
  day: string;
  // The workout-exercise row id (WorkoutExerciseResponse.id), NOT the catalog slug.
  workoutExerciseId: string;
}

export function useRemoveExercise(workoutId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ day, workoutExerciseId }: RemoveExercisePayload) =>
      apiFetch<void>(
        `/workouts/${workoutId}/training-days/${day}/exercises/${workoutExerciseId}`,
        { method: 'DELETE' },
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workouts', workoutId] }),
  });
}
