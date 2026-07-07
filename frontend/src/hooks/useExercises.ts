import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { ExerciseResponse, WorkoutExerciseResponse, TrainingDayResponse, WorkoutResponse } from '../types/api';

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

interface ReorderExercisesPayload {
  orderedExerciseIds: string[];
}

export function useReorderExercises(workoutId: string, day: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orderedExerciseIds }: ReorderExercisesPayload) =>
      apiFetch<TrainingDayResponse>(
        `/workouts/${workoutId}/training-days/${day}/exercises/reorder`,
        {
          method: 'PUT',
          body: JSON.stringify({ ordered_exercise_ids: orderedExerciseIds }),
        },
      ),
    onMutate: async ({ orderedExerciseIds }) => {
      await qc.cancelQueries({ queryKey: ['workouts', workoutId] });
      const previous = qc.getQueryData<WorkoutResponse>(['workouts', workoutId]);
      if (previous) {
        qc.setQueryData<WorkoutResponse>(['workouts', workoutId], {
          ...previous,
          training_days: previous.training_days.map((td) =>
            td.day_of_week === day
              ? {
                  ...td,
                  exercises: orderedExerciseIds.flatMap((exId, i) => {
                    const ex = td.exercises.find((e) => e.id === exId);
                    return ex ? [{ ...ex, order: i + 1 }] : [];
                  }),
                }
              : td,
          ),
        });
      }
      return { previous };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.previous) qc.setQueryData(['workouts', workoutId], ctx.previous);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['workouts', workoutId] }),
  });
}
