import { renderHook, waitFor, act } from '@testing-library/react';
import { apiFetch } from '../lib/api';
import { createWrapper } from '../test/test-utils';
import {
  useUserPreferences,
  useUpdatePreferences,
} from './useUserPreferences';
import type { UserPreferences } from './useUserPreferences';
import type { UserResponse } from '../types/api';

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

function makePreferences(): UserPreferences {
  return { rest_seconds: 90, units: 'kg' };
}

function makeUserResponse(): UserResponse {
  return {
    id: 'user-1',
    email: 'test@example.com',
    created_at: '2024-01-01T00:00:00Z',
    rest_seconds: 120,
    units: 'lb',
  };
}

// ---------------------------------------------------------------------------
// useUserPreferences
// ---------------------------------------------------------------------------

describe('useUserPreferences', () => {
  it('fetches and returns user preferences from /auth/me', async () => {
    const prefs = makePreferences();
    vi.mocked(apiFetch).mockResolvedValue(prefs);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useUserPreferences(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(prefs);
    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith('/auth/me');
  });

  it('is in error state when apiFetch rejects', async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error('Unauthorized'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useUserPreferences(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

// ---------------------------------------------------------------------------
// useUpdatePreferences
// ---------------------------------------------------------------------------

describe('useUpdatePreferences', () => {
  it('calls PATCH /users/me/preferences with the updated payload', async () => {
    vi.mocked(apiFetch).mockResolvedValue(makeUserResponse());

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useUpdatePreferences(), { wrapper });

    await act(async () => {
      result.current.mutate({ rest_seconds: 120, units: 'lb' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/users/me/preferences',
      {
        method: 'PATCH',
        body: JSON.stringify({ rest_seconds: 120, units: 'lb' }),
      },
    );
  });

  it("invalidates ['user', 'me'] on success", async () => {
    vi.mocked(apiFetch).mockResolvedValue(makeUserResponse());

    const { wrapper, queryClient } = createWrapper();
    const { result } = renderHook(() => useUpdatePreferences(), { wrapper });
    const spy = vi.spyOn(queryClient, 'invalidateQueries');

    await act(async () => {
      result.current.mutate({ rest_seconds: 60 });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(spy).toHaveBeenCalledWith({ queryKey: ['user', 'me'] });
  });

  it('surfaces error when apiFetch rejects', async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error('Validation failed'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useUpdatePreferences(), { wrapper });

    await act(async () => {
      result.current.mutate({ units: 'lb' });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(Error);
  });
});
