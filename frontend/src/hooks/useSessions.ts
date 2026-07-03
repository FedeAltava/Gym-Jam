import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type {
  WorkoutSessionResponse,
  ExerciseLogResponse,
} from '../types/api';

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

export function useSessionsForDay(workoutId: string, dayId: string) {
  return useQuery({
    queryKey: ['sessions', workoutId, dayId],
    queryFn: () =>
      apiFetch<WorkoutSessionResponse[]>(
        `/workouts/${workoutId}/days/${dayId}/sessions`,
      ),
    enabled: !!workoutId && !!dayId,
  });
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

interface StartSessionContext {
  workoutId: string;
  dayId: string;
}

export function useStartSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ workoutId, dayId }: StartSessionContext) =>
      apiFetch<WorkoutSessionResponse>(
        `/workouts/${workoutId}/days/${dayId}/sessions`,
        { method: 'POST', body: JSON.stringify({}) },
      ),
    onSuccess: (_data, { workoutId, dayId }) => {
      qc.invalidateQueries({ queryKey: ['sessions', workoutId, dayId] });
    },
  });
}

interface LogSetPayload {
  sessionId: string;
  workoutExerciseId: string;
  setNumber: number;
  repsCompleted: number;
  weightKg: number | null;
  // context for cache invalidation
  workoutId: string;
  dayId: string;
}

export function useLogSet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      workoutExerciseId,
      setNumber,
      repsCompleted,
      weightKg,
    }: LogSetPayload) =>
      apiFetch<ExerciseLogResponse>(`/sessions/${sessionId}/logs`, {
        method: 'POST',
        body: JSON.stringify({
          workout_exercise_id: workoutExerciseId,
          set_number: setNumber,
          reps_completed: repsCompleted,
          weight_kg: weightKg,
        }),
      }),
    onSuccess: (_data, { workoutId, dayId }) => {
      qc.invalidateQueries({ queryKey: ['sessions', workoutId, dayId] });
    },
  });
}

interface CompleteSessionContext {
  sessionId: string;
  workoutId: string;
  dayId: string;
}

export function useCompleteSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId }: CompleteSessionContext) =>
      apiFetch<WorkoutSessionResponse>(`/sessions/${sessionId}/complete`, {
        method: 'POST',
        body: JSON.stringify({}),
      }),
    onSuccess: (_data, { workoutId, dayId }) => {
      qc.invalidateQueries({ queryKey: ['sessions', workoutId, dayId] });
    },
  });
}
