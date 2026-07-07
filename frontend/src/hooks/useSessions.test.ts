import { renderHook, waitFor, act } from '@testing-library/react';
import { apiFetch } from '../lib/api';
import { createWrapper } from '../test/test-utils';
import {
  useLogSet,
  useUpdateLog,
  useCompleteSession,
} from './useSessions';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

afterEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// useLogSet
// ---------------------------------------------------------------------------

describe('useLogSet', () => {
  it('POSTs /sessions/:sessionId/logs with snake_case body', async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'log-1' });
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLogSet(), { wrapper });

    await act(async () => {
      result.current.mutate({
        sessionId: 'sess-1',
        workoutExerciseId: 'we-1',
        setNumber: 1,
        repsCompleted: 10,
        weightKg: 80,
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith('/sessions/sess-1/logs', {
      method: 'POST',
      body: JSON.stringify({
        workout_exercise_id: 'we-1',
        set_number: 1,
        reps_completed: 10,
        weight_kg: 80,
      }),
    });
  });

  it('allows weightKg null (bodyweight set) — request IS sent with weight_kg: null', async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'log-2' });
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLogSet(), { wrapper });

    await act(async () => {
      result.current.mutate({
        sessionId: 'sess-1',
        workoutExerciseId: 'we-1',
        setNumber: 1,
        repsCompleted: 5,
        weightKg: null,
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith('/sessions/sess-1/logs', {
      method: 'POST',
      body: JSON.stringify({
        workout_exercise_id: 'we-1',
        set_number: 1,
        reps_completed: 5,
        weight_kg: null,
      }),
    });
  });

  it('rejects weightKg NaN WITHOUT calling apiFetch', async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLogSet(), { wrapper });

    await act(async () => {
      result.current.mutate({
        sessionId: 'sess-1',
        workoutExerciseId: 'we-1',
        setNumber: 1,
        repsCompleted: 10,
        weightKg: NaN,
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(vi.mocked(apiFetch)).not.toHaveBeenCalled();
  });

  it('rejects negative weightKg without calling apiFetch', async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLogSet(), { wrapper });

    await act(async () => {
      result.current.mutate({
        sessionId: 'sess-1',
        workoutExerciseId: 'we-1',
        setNumber: 1,
        repsCompleted: 10,
        weightKg: -5,
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(vi.mocked(apiFetch)).not.toHaveBeenCalled();
  });

  it('rejects repsCompleted 0 and non-integer reps without calling apiFetch', async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLogSet(), { wrapper });

    await act(async () => {
      result.current.mutate({
        sessionId: 'sess-1',
        workoutExerciseId: 'we-1',
        setNumber: 1,
        repsCompleted: 0,
        weightKg: 80,
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(vi.mocked(apiFetch)).not.toHaveBeenCalled();

    // Non-integer
    vi.clearAllMocks();
    const { result: result2 } = renderHook(() => useLogSet(), { wrapper });

    await act(async () => {
      result2.current.mutate({
        sessionId: 'sess-1',
        workoutExerciseId: 'we-1',
        setNumber: 1,
        repsCompleted: 2.5,
        weightKg: 80,
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result2.current.isError).toBe(true));
    expect(vi.mocked(apiFetch)).not.toHaveBeenCalled();
  });

  it("invalidates ['sessions', workoutId, dayId] on success", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'log-3' });
    const { wrapper, queryClient } = createWrapper();
    const { result } = renderHook(() => useLogSet(), { wrapper });
    const spy = vi.spyOn(queryClient, 'invalidateQueries');

    await act(async () => {
      result.current.mutate({
        sessionId: 'sess-1',
        workoutExerciseId: 'we-1',
        setNumber: 1,
        repsCompleted: 8,
        weightKg: 60,
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledWith({ queryKey: ['sessions', 'wk-1', 'day-1'] });
  });

  it('exposes the error via mutation.isError when apiFetch rejects', async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error('Network error'));
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLogSet(), { wrapper });

    await act(async () => {
      result.current.mutate({
        sessionId: 'sess-1',
        workoutExerciseId: 'we-1',
        setNumber: 1,
        repsCompleted: 5,
        weightKg: 50,
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// useUpdateLog
// ---------------------------------------------------------------------------

describe('useUpdateLog', () => {
  it('sends only reps_completed when weightKg is undefined (field omitted)', async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'log-1' });
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useUpdateLog(), { wrapper });

    await act(async () => {
      result.current.mutate({
        sessionId: 'sess-1',
        logId: 'log-1',
        repsCompleted: 12,
        weightKg: undefined,
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/sessions/sess-1/logs/log-1',
      {
        method: 'PATCH',
        body: JSON.stringify({ reps_completed: 12 }),
      },
    );
  });

  it('sends weight_kg: null when weightKg is explicitly null (intentional clear to bodyweight)', async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'log-1' });
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useUpdateLog(), { wrapper });

    await act(async () => {
      result.current.mutate({
        sessionId: 'sess-1',
        logId: 'log-1',
        repsCompleted: undefined,
        weightKg: null,
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/sessions/sess-1/logs/log-1',
      {
        method: 'PATCH',
        body: JSON.stringify({ weight_kg: null }),
      },
    );
  });

  it('rejects without network call when both fields are invalid/undefined', async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useUpdateLog(), { wrapper });

    await act(async () => {
      result.current.mutate({
        sessionId: 'sess-1',
        logId: 'log-1',
        repsCompleted: undefined,
        weightKg: undefined,
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(vi.mocked(apiFetch)).not.toHaveBeenCalled();
  });

  it('NaN weightKg with no reps is rejected, never serialized as null', async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useUpdateLog(), { wrapper });

    await act(async () => {
      result.current.mutate({
        sessionId: 'sess-1',
        logId: 'log-1',
        repsCompleted: undefined,
        weightKg: NaN,
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(vi.mocked(apiFetch)).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// useCompleteSession
// ---------------------------------------------------------------------------

describe('useCompleteSession', () => {
  it('POSTs /sessions/:id/complete and invalidates the correct query key', async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'sess-1', completed_at: '2024-01-01' });
    const { wrapper, queryClient } = createWrapper();
    const { result } = renderHook(() => useCompleteSession(), { wrapper });
    const spy = vi.spyOn(queryClient, 'invalidateQueries');

    await act(async () => {
      result.current.mutate({
        sessionId: 'sess-1',
        workoutId: 'wk-1',
        dayId: 'day-1',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith('/sessions/sess-1/complete', {
      method: 'POST',
      body: JSON.stringify({}),
    });
    expect(spy).toHaveBeenCalledWith({ queryKey: ['sessions', 'wk-1', 'day-1'] });
  });
});
