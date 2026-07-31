import { renderHook, waitFor, act } from '@testing-library/react';
import { apiFetch } from '../lib/api';
import { createWrapper } from '../test/test-utils';
import { useChangePassword } from './useProfile';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

afterEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// useChangePassword
// ---------------------------------------------------------------------------

describe('useChangePassword', () => {
  it('calls PATCH /auth/password with current and new password', async () => {
    vi.mocked(apiFetch).mockResolvedValue(undefined);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useChangePassword(), { wrapper });

    await act(async () => {
      result.current.mutate({
        current_password: 'old-pass',
        new_password: 'new-pass',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/auth/password',
      {
        method: 'PATCH',
        body: JSON.stringify({ current_password: 'old-pass', new_password: 'new-pass' }),
      },
    );
  });

  it('is in idle state before mutation is triggered', () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useChangePassword(), { wrapper });

    expect(result.current.isIdle).toBe(true);
    expect(result.current.isSuccess).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it('surfaces error when apiFetch rejects', async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error('Wrong password'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useChangePassword(), { wrapper });

    await act(async () => {
      result.current.mutate({
        current_password: 'wrong',
        new_password: 'new-pass',
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(Error);
  });
});
