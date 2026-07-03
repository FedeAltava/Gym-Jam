import {
  useQuery,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { WorkoutResponse } from '../types/api';

interface CreateWorkoutPayload {
  name: string;
  description?: string;
  training_days: string[];
}

const PAGE_SIZE = 20;

export function useWorkouts() {
  return useInfiniteQuery({
    queryKey: ['workouts'],
    queryFn: ({ pageParam }) =>
      apiFetch<WorkoutResponse[]>(`/workouts?limit=${PAGE_SIZE}&offset=${pageParam}`),
    initialPageParam: 0,
    // The endpoint returns a bare array (no total): a full page means there
    // may be more; a short page means we reached the end.
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length === PAGE_SIZE ? allPages.length * PAGE_SIZE : undefined,
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
