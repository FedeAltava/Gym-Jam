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
  weightKg: number;
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
    }: LogSetPayload) => {
      // Last line of defense: JSON.stringify(NaN) serializes to null, which
      // the API rejects with 422 (weight_kg is a required float). Fail loudly
      // here instead of sending an invalid body.
      if (!Number.isFinite(weightKg) || weightKg < 0) {
        return Promise.reject(
          new Error('El peso debe ser un número válido de 0 o más kg.'),
        );
      }
      if (!Number.isInteger(repsCompleted) || repsCompleted < 1) {
        return Promise.reject(
          new Error('Las repeticiones deben ser un entero de 1 o más.'),
        );
      }
      return apiFetch<ExerciseLogResponse>(`/sessions/${sessionId}/logs`, {
        method: 'POST',
        body: JSON.stringify({
          workout_exercise_id: workoutExerciseId,
          set_number: setNumber,
          reps_completed: repsCompleted,
          weight_kg: weightKg,
        }),
      });
    },
    onSuccess: (_data, { workoutId, dayId }) => {
      qc.invalidateQueries({ queryKey: ['sessions', workoutId, dayId] });
    },
  });
}

interface UpdateLogData {
  repsCompleted?: number;
  weightKg?: number;
}

interface UpdateLogPayload extends UpdateLogData {
  sessionId: string;
  logId: string;
  // context for cache invalidation
  workoutId: string;
  dayId: string;
}

function updateLog(
  sessionId: string,
  logId: string,
  data: UpdateLogData,
): Promise<ExerciseLogResponse> {
  // NaN would serialize to null, which the PATCH schema treats as "field not
  // provided" — the update would silently do nothing. Only include fields
  // that hold real numbers, and require at least one of them.
  const repsValid = Number.isInteger(data.repsCompleted);
  const weightValid = Number.isFinite(data.weightKg);
  if (!repsValid && !weightValid) {
    return Promise.reject(
      new Error('Ingresa nuevas repeticiones o un nuevo peso para actualizar.'),
    );
  }
  return apiFetch<ExerciseLogResponse>(`/sessions/${sessionId}/logs/${logId}`, {
    method: 'PATCH',
    body: JSON.stringify({
      ...(repsValid && { reps_completed: data.repsCompleted }),
      ...(weightValid && { weight_kg: data.weightKg }),
    }),
  });
}

export function useUpdateLog() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, logId, repsCompleted, weightKg }: UpdateLogPayload) =>
      updateLog(sessionId, logId, { repsCompleted, weightKg }),
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

interface DeleteSessionContext {
  sessionId: string;
  // context for cache invalidation
  workoutId: string;
  dayId: string;
}

export function useDeleteSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId }: DeleteSessionContext) =>
      apiFetch<void>(`/sessions/${sessionId}`, { method: 'DELETE' }),
    onSuccess: (_data, { workoutId, dayId }) => {
      qc.invalidateQueries({ queryKey: ['sessions', workoutId, dayId] });
    },
  });
}
