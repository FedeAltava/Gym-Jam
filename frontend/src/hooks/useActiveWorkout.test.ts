import { renderHook, waitFor } from '@testing-library/react';
import { apiFetch } from '../lib/api';
import { createWrapper } from '../test/test-utils';
import { useActiveWorkout } from './useActiveWorkout';
import type { WorkoutResponse } from '../types/api';

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

function makeWorkout(id: string, isActive: boolean): WorkoutResponse {
  return {
    id,
    name: `Workout ${id}`,
    description: null,
    is_active: isActive,
    training_days: [],
  };
}

// ---------------------------------------------------------------------------
// useActiveWorkout
// ---------------------------------------------------------------------------

describe('useActiveWorkout', () => {
  it('returns the active workout when one exists', async () => {
    const active = makeWorkout('wk-active', true);
    const inactive = makeWorkout('wk-inactive', false);
    vi.mocked(apiFetch).mockResolvedValue([inactive, active]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useActiveWorkout(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.activeWorkout).toEqual(active);
  });

  it('returns undefined when no active workout exists', async () => {
    const w1 = makeWorkout('wk-1', false);
    const w2 = makeWorkout('wk-2', false);
    vi.mocked(apiFetch).mockResolvedValue([w1, w2]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useActiveWorkout(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.activeWorkout).toBeUndefined();
  });

  it('returns undefined when the workout list is empty', async () => {
    vi.mocked(apiFetch).mockResolvedValue([]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useActiveWorkout(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.activeWorkout).toBeUndefined();
  });

  it('has isLoading true while pending and false after resolve', async () => {
    let resolveFetch!: (value: WorkoutResponse[]) => void;
    const pendingPromise = new Promise<WorkoutResponse[]>((resolve) => {
      resolveFetch = resolve;
    });
    vi.mocked(apiFetch).mockReturnValue(pendingPromise);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useActiveWorkout(), { wrapper });

    expect(result.current.isLoading).toBe(true);

    resolveFetch([]);

    await waitFor(() => expect(result.current.isLoading).toBe(false));
  });

  it('has isError true when apiFetch rejects', async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error('Network error'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useActiveWorkout(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.activeWorkout).toBeUndefined();
  });

  it('calls the correct URL with limit=100&offset=0', async () => {
    vi.mocked(apiFetch).mockResolvedValue([]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useActiveWorkout(), { wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/workouts?limit=100&offset=0',
    );
  });
});
