import { renderHook, waitFor, act } from '@testing-library/react';
import { apiFetch } from '../lib/api';
import { createWrapper } from '../test/test-utils';
import {
  useAddTrainingDay,
  useRemoveTrainingDay,
  useReorderTrainingDays,
  useSetWorkoutActive,
} from './useWorkouts';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

afterEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// useAddTrainingDay
// ---------------------------------------------------------------------------

describe('useAddTrainingDay', () => {
  it('POSTs /workouts/:id/training-days with body { day_of_week }', async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'wk-1' });
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useAddTrainingDay('wk-1'), { wrapper });

    await act(async () => {
      result.current.mutate('monday');
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/workouts/wk-1/training-days',
      {
        method: 'POST',
        body: JSON.stringify({ day_of_week: 'monday' }),
      },
    );
  });

  it("invalidates ['workouts', workoutId] on success", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'wk-1' });
    const { wrapper, queryClient } = createWrapper();
    const { result } = renderHook(() => useAddTrainingDay('wk-1'), { wrapper });
    const spy = vi.spyOn(queryClient, 'invalidateQueries');

    await act(async () => {
      result.current.mutate('tuesday');
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledWith({ queryKey: ['workouts', 'wk-1'] });
  });

  it('exposes error when the request fails', async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error('Server error'));
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useAddTrainingDay('wk-1'), { wrapper });

    await act(async () => {
      result.current.mutate('wednesday');
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(Error);
  });
});

// ---------------------------------------------------------------------------
// useRemoveTrainingDay
// ---------------------------------------------------------------------------

describe('useRemoveTrainingDay', () => {
  it('DELETEs /workouts/:id/training-days/:day (day in the path, not body)', async () => {
    vi.mocked(apiFetch).mockResolvedValue(undefined);
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useRemoveTrainingDay('wk-1'), { wrapper });

    await act(async () => {
      result.current.mutate('monday');
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/workouts/wk-1/training-days/monday',
      { method: 'DELETE' },
    );
  });

  it("invalidates ['workouts', workoutId] on success", async () => {
    vi.mocked(apiFetch).mockResolvedValue(undefined);
    const { wrapper, queryClient } = createWrapper();
    const { result } = renderHook(() => useRemoveTrainingDay('wk-1'), { wrapper });
    const spy = vi.spyOn(queryClient, 'invalidateQueries');

    await act(async () => {
      result.current.mutate('friday');
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledWith({ queryKey: ['workouts', 'wk-1'] });
  });
});

// ---------------------------------------------------------------------------
// useReorderTrainingDays
// ---------------------------------------------------------------------------

describe('useReorderTrainingDays', () => {
  it('PUTs ordered_day_ids (snake_case) from the camelCase input', async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'wk-1' });
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useReorderTrainingDays('wk-1'), { wrapper });

    const orderedDayIds = ['day-3', 'day-1', 'day-2'];

    await act(async () => {
      result.current.mutate({ orderedDayIds });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/workouts/wk-1/training-days/reorder',
      {
        method: 'PUT',
        body: JSON.stringify({ ordered_day_ids: orderedDayIds }),
      },
    );
  });
});

// ---------------------------------------------------------------------------
// useSetWorkoutActive
// ---------------------------------------------------------------------------

describe('useSetWorkoutActive', () => {
  it("invalidates both ['workouts', workoutId] AND the ['workouts'] list key on success", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ id: 'wk-1', is_active: true });
    const { wrapper, queryClient } = createWrapper();
    const { result } = renderHook(() => useSetWorkoutActive('wk-1'), { wrapper });
    const spy = vi.spyOn(queryClient, 'invalidateQueries');

    await act(async () => {
      result.current.mutate(true);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(spy).toHaveBeenCalledWith({ queryKey: ['workouts', 'wk-1'] });
    expect(spy).toHaveBeenCalledWith({ queryKey: ['workouts'] });
  });
});
