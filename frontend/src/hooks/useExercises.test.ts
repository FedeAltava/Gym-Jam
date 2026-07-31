import { renderHook, waitFor, act } from '@testing-library/react';
import { apiFetch } from '../lib/api';
import { createWrapper } from '../test/test-utils';
import {
  useExercises,
  useAddExercise,
  useRemoveExercise,
  useBatchAddExercises,
} from './useExercises';
import type { ExerciseResponse, WorkoutExerciseResponse } from '../types/api';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

afterEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeExercise(id: string): ExerciseResponse {
  return {
    id,
    name: `Exercise ${id}`,
    muscle_group: 'chest',
    is_bodyweight: false,
  };
}

function makeWorkoutExercise(id: string): WorkoutExerciseResponse {
  return {
    id,
    exercise_id: `catalog-${id}`,
    order: 1,
    sets: 3,
    reps_per_set: 10,
    weight_kg: null,
  };
}

// ---------------------------------------------------------------------------
// useExercises
// ---------------------------------------------------------------------------

describe('useExercises', () => {
  it('fetches and returns the full exercise list from /exercises', async () => {
    const exercises = [makeExercise('ex-1'), makeExercise('ex-2')];
    vi.mocked(apiFetch).mockResolvedValue(exercises);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useExercises(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(exercises);
    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith('/exercises');
  });

  it('fetches from /exercises?muscle_group=... when a muscle group is passed', async () => {
    const exercises = [makeExercise('ex-chest')];
    vi.mocked(apiFetch).mockResolvedValue(exercises);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useExercises('chest'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith('/exercises?muscle_group=chest');
  });

  it('is in error state when apiFetch rejects', async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error('Server error'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useExercises(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

// ---------------------------------------------------------------------------
// useAddExercise
// ---------------------------------------------------------------------------

describe('useAddExercise', () => {
  it('POSTs to the correct training-day exercises endpoint', async () => {
    vi.mocked(apiFetch).mockResolvedValue(makeWorkoutExercise('we-1'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useAddExercise('wk-1'), { wrapper });

    await act(async () => {
      result.current.mutate({ day: 'monday', exerciseId: 'catalog-1' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/workouts/wk-1/training-days/monday/exercises',
      {
        method: 'POST',
        body: JSON.stringify({ exercise_id: 'catalog-1' }),
      },
    );
  });

  it("invalidates ['workouts', workoutId] on success", async () => {
    vi.mocked(apiFetch).mockResolvedValue(makeWorkoutExercise('we-1'));

    const { wrapper, queryClient } = createWrapper();
    const { result } = renderHook(() => useAddExercise('wk-1'), { wrapper });
    const spy = vi.spyOn(queryClient, 'invalidateQueries');

    await act(async () => {
      result.current.mutate({ day: 'monday', exerciseId: 'catalog-1' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledWith({ queryKey: ['workouts', 'wk-1'] });
  });

  it('surfaces error when the request fails', async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error('Not found'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useAddExercise('wk-1'), { wrapper });

    await act(async () => {
      result.current.mutate({ day: 'monday', exerciseId: 'bad-id' });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

// ---------------------------------------------------------------------------
// useRemoveExercise
// ---------------------------------------------------------------------------

describe('useRemoveExercise', () => {
  it('DELETEs the correct workout-exercise resource', async () => {
    vi.mocked(apiFetch).mockResolvedValue(undefined);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useRemoveExercise('wk-1'), { wrapper });

    await act(async () => {
      result.current.mutate({ day: 'monday', workoutExerciseId: 'we-1' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/workouts/wk-1/training-days/monday/exercises/we-1',
      { method: 'DELETE' },
    );
  });

  it("invalidates ['workouts', workoutId] on success", async () => {
    vi.mocked(apiFetch).mockResolvedValue(undefined);

    const { wrapper, queryClient } = createWrapper();
    const { result } = renderHook(() => useRemoveExercise('wk-1'), { wrapper });
    const spy = vi.spyOn(queryClient, 'invalidateQueries');

    await act(async () => {
      result.current.mutate({ day: 'monday', workoutExerciseId: 'we-1' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledWith({ queryKey: ['workouts', 'wk-1'] });
  });
});

// ---------------------------------------------------------------------------
// useBatchAddExercises
// ---------------------------------------------------------------------------

describe('useBatchAddExercises', () => {
  it('calls apiFetch once per exercise in the batch (sequential adds, all succeed)', async () => {
    vi.mocked(apiFetch)
      .mockResolvedValueOnce(makeWorkoutExercise('we-1'))
      .mockResolvedValueOnce(makeWorkoutExercise('we-2'))
      .mockResolvedValueOnce(makeWorkoutExercise('we-3'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useBatchAddExercises('wk-1'), { wrapper });

    await act(async () => {
      result.current.mutate({ dayId: 'day-1', exerciseIds: ['cat-1', 'cat-2', 'cat-3'] });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledTimes(3);
    expect(vi.mocked(apiFetch)).toHaveBeenNthCalledWith(
      1,
      '/workouts/wk-1/training-days/day-1/exercises',
      { method: 'POST', body: JSON.stringify({ exercise_id: 'cat-1' }) },
    );
    expect(vi.mocked(apiFetch)).toHaveBeenNthCalledWith(
      2,
      '/workouts/wk-1/training-days/day-1/exercises',
      { method: 'POST', body: JSON.stringify({ exercise_id: 'cat-2' }) },
    );
    expect(vi.mocked(apiFetch)).toHaveBeenNthCalledWith(
      3,
      '/workouts/wk-1/training-days/day-1/exercises',
      { method: 'POST', body: JSON.stringify({ exercise_id: 'cat-3' }) },
    );
  });

  it("invalidates ['workouts', workoutId] on success", async () => {
    vi.mocked(apiFetch).mockResolvedValue(makeWorkoutExercise('we-1'));

    const { wrapper, queryClient } = createWrapper();
    const { result } = renderHook(() => useBatchAddExercises('wk-1'), { wrapper });
    const spy = vi.spyOn(queryClient, 'invalidateQueries');

    await act(async () => {
      result.current.mutate({ dayId: 'day-1', exerciseIds: ['cat-1'] });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledWith({ queryKey: ['workouts', 'wk-1'] });
  });

  it('stops on the first failure and enters error state (partial failure)', async () => {
    // First add succeeds, second fails — third must never be called.
    vi.mocked(apiFetch)
      .mockResolvedValueOnce(makeWorkoutExercise('we-1'))
      .mockRejectedValueOnce(new Error('Conflict'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useBatchAddExercises('wk-1'), { wrapper });

    await act(async () => {
      result.current.mutate({ dayId: 'day-1', exerciseIds: ['cat-1', 'cat-2', 'cat-3'] });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    // Only the first two calls were made — the loop threw on the second, so the
    // third was never reached.
    expect(vi.mocked(apiFetch)).toHaveBeenCalledTimes(2);
    expect(result.current.error).toBeInstanceOf(Error);
  });
});
