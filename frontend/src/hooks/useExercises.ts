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
    staleTime: 1000 * 60 * 5,
  });
}

interface CreateExercisePayload {
  name: string;
  muscle_group: string;
  is_bodyweight?: boolean;
}

export function useCreateExercise() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateExercisePayload) =>
      apiFetch<ExerciseResponse>('/exercises', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['exercises'] }),
  });
}

export function useDeleteExercise() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (exerciseId: string) =>
      apiFetch<void>(`/exercises/${exerciseId}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['exercises'] }),
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
