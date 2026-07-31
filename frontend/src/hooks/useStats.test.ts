import { renderHook, waitFor } from '@testing-library/react';
import { apiFetch } from '../lib/api';
import { createWrapper } from '../test/test-utils';
import { useUserStats } from './useStats';
import type { UserStats } from '../types/api';

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

function makeStats(): UserStats {
  return {
    total_sessions: 42,
    streak: 5,
    total_prs: 10,
    weekly_volume_kg: 1500,
    weekly_sessions: 3,
    weekly_prs: 2,
  };
}

// ---------------------------------------------------------------------------
// useUserStats
// ---------------------------------------------------------------------------

describe('useUserStats', () => {
  it('fetches and returns stats from /users/me/stats', async () => {
    const stats = makeStats();
    vi.mocked(apiFetch).mockResolvedValue(stats);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useUserStats(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(stats);
    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith('/users/me/stats');
  });

  it('has isLoading true while pending and false after resolve', async () => {
    let resolveStats!: (value: UserStats) => void;
    const pendingPromise = new Promise<UserStats>((resolve) => {
      resolveStats = resolve;
    });
    vi.mocked(apiFetch).mockReturnValue(pendingPromise);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useUserStats(), { wrapper });

    expect(result.current.isLoading).toBe(true);

    resolveStats(makeStats());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.isSuccess).toBe(true);
  });

  it('has isError true and no data when apiFetch rejects', async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error('Unauthorized'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useUserStats(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.data).toBeUndefined();
  });
});
