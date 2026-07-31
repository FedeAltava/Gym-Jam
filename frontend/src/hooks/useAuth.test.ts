import { renderHook, waitFor, act } from '@testing-library/react';
import { apiFetch } from '../lib/api';
import { createWrapper } from '../test/test-utils';
import {
  useLoginMutation,
  useLogout,
  useRegisterMutation,
} from './useAuth';
import { useAuthStore } from '../store/authStore';
import type { TokenResponse, UserResponse } from '../types/api';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

// Mock react-router-dom navigate — the hooks call useNavigate() internally.
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => ({
  ...(await orig()),
  useNavigate: () => mockNavigate,
}));

afterEach(() => {
  vi.clearAllMocks();
  // Reset Zustand auth store state between tests.
  useAuthStore.setState({ token: null, user: null });
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const mockToken: TokenResponse = {
  access_token: 'test-access-token',
  token_type: 'bearer',
};

const mockUser: UserResponse = {
  id: 'user-1',
  email: 'test@example.com',
  created_at: '2024-01-01T00:00:00Z',
  rest_seconds: 90,
  units: 'kg',
};

// ---------------------------------------------------------------------------
// useLoginMutation
// ---------------------------------------------------------------------------

describe('useLoginMutation', () => {
  it('calls /auth/login with credentials then fetches /auth/me', async () => {
    vi.mocked(apiFetch)
      .mockResolvedValueOnce(mockToken)  // POST /auth/login
      .mockResolvedValueOnce(mockUser);  // GET /auth/me

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLoginMutation(), { wrapper });

    await act(async () => {
      result.current.mutate({ email: 'test@example.com', password: 'secret' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenNthCalledWith(
      1,
      '/auth/login',
      { method: 'POST', body: JSON.stringify({ email: 'test@example.com', password: 'secret' }) },
    );
    expect(vi.mocked(apiFetch)).toHaveBeenNthCalledWith(
      2,
      '/auth/me',
      { headers: { Authorization: 'Bearer test-access-token' } },
    );
  });

  it('updates the auth store with token and user on success', async () => {
    vi.mocked(apiFetch)
      .mockResolvedValueOnce(mockToken)
      .mockResolvedValueOnce(mockUser);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLoginMutation(), { wrapper });

    await act(async () => {
      result.current.mutate({ email: 'test@example.com', password: 'secret' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const state = useAuthStore.getState();
    expect(state.token).toBe('test-access-token');
    expect(state.user).toEqual(mockUser);
  });

  it('navigates to /dashboard on success', async () => {
    vi.mocked(apiFetch)
      .mockResolvedValueOnce(mockToken)
      .mockResolvedValueOnce(mockUser);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLoginMutation(), { wrapper });

    await act(async () => {
      result.current.mutate({ email: 'test@example.com', password: 'secret' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  it('surfaces error when login fails', async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error('Invalid credentials'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLoginMutation(), { wrapper });

    await act(async () => {
      result.current.mutate({ email: 'bad@example.com', password: 'wrong' });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(Error);
    // Auth store must not be modified on failure.
    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// useLogout
// ---------------------------------------------------------------------------

describe('useLogout', () => {
  it('calls POST /auth/logout', async () => {
    vi.mocked(apiFetch).mockResolvedValue(undefined);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLogout(), { wrapper });

    await act(async () => {
      result.current.mutate();
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/auth/logout',
      { method: 'POST' },
    );
  });

  it('clears the auth store and navigates to /login on settled', async () => {
    // Pre-populate the store to verify it is cleared.
    useAuthStore.setState({ token: 'existing-token', user: mockUser });

    vi.mocked(apiFetch).mockResolvedValue(undefined);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLogout(), { wrapper });

    await act(async () => {
      result.current.mutate();
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('still clears store and navigates to /login even when API call fails', async () => {
    useAuthStore.setState({ token: 'existing-token', user: mockUser });

    vi.mocked(apiFetch).mockRejectedValue(new Error('Network error'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useLogout(), { wrapper });

    await act(async () => {
      result.current.mutate();
    });

    // onSettled fires regardless of success/failure.
    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });
});

// ---------------------------------------------------------------------------
// useRegisterMutation
// ---------------------------------------------------------------------------

describe('useRegisterMutation', () => {
  it('calls POST /auth/register with credentials', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockUser);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useRegisterMutation(), { wrapper });

    await act(async () => {
      result.current.mutate({ email: 'new@example.com', password: 'newpass' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/auth/register',
      { method: 'POST', body: JSON.stringify({ email: 'new@example.com', password: 'newpass' }) },
    );
  });

  it('navigates to /login on successful registration', async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockUser);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useRegisterMutation(), { wrapper });

    await act(async () => {
      result.current.mutate({ email: 'new@example.com', password: 'newpass' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('surfaces error when registration fails', async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error('Email already exists'));

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useRegisterMutation(), { wrapper });

    await act(async () => {
      result.current.mutate({ email: 'existing@example.com', password: 'pass' });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(Error);
  });
});
