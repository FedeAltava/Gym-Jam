import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { WorkoutResponse } from '../types/api';

interface CreateWorkoutPayload {
  name: string;
  description?: string;
  training_days: string[];
}

export function useWorkouts() {
  return useQuery({
    queryKey: ['workouts'],
    queryFn: () => apiFetch<WorkoutResponse[]>('/workouts'),
  });
}

export function useWorkout(id: string) {
  return useQuery({
    queryKey: ['workouts', id],
    queryFn: () => apiFetch<WorkoutResponse>(`/workouts/${id}`),
    enabled: !!id,
  });
}

export function useCreateWorkout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateWorkoutPayload) =>
      apiFetch<WorkoutResponse>('/workouts', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['workouts'] }),
  });
}
