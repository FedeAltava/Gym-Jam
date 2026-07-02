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
    // Request the backend max explicitly (default is 50). Pagination UI is
    // future work for when users exceed 100 workouts.
    queryFn: () => apiFetch<WorkoutResponse[]>('/workouts?limit=100'),
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
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateWorkoutPayload) =>
      apiFetch<WorkoutResponse>('/workouts', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workouts'] }),
  });
}

export function useDeleteWorkout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/workouts/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workouts'] }),
  });
}
