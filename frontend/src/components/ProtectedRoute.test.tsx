import { screen, waitFor } from '@testing-library/react';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { useAuthStore } from '../store/authStore';

// ProtectedRoute uses native `fetch` (not apiFetch) for the silent-refresh call.
// We intercept it via vi.stubGlobal.

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const REFRESH_URL = 'http://test.local/auth/refresh';

const TEST_USER = {
  id: 'u1',
  email: 'test@example.com',
  created_at: '2026-01-01T00:00:00Z',
  rest_seconds: 90,
  units: 'kg' as const,
};

/** Minimal fetch mock factory. */
function makeFetchMock(
  responseFactory: () => { status: number; ok: boolean; json?: () => Promise<unknown> },
) {
  return vi.fn((url: string) => {
    if (url === REFRESH_URL) {
      const res = responseFactory();
      return Promise.resolve({
        status: res.status,
        ok: res.ok,
        json: res.json ?? (() => Promise.resolve({})),
      });
    }
    return Promise.resolve({ status: 404, ok: false, json: () => Promise.resolve({}) });
  });
}

/** Render ProtectedRoute inside a MemoryRouter so Navigate can work. */
function renderProtectedRoute(children: React.ReactNode = <div>Protected content</div>) {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <ProtectedRoute>{children}</ProtectedRoute>
    </MemoryRouter>,
  );
}

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  // Reset store to fully unauthenticated state before each test
  useAuthStore.setState({ token: null, user: null });
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ProtectedRoute', () => {
  it('renders children when token and user are in store', () => {
    useAuthStore.setState({ token: 'valid-token', user: TEST_USER });

    renderProtectedRoute();

    // Children are shown immediately — no redirect, no loading
    expect(screen.getByText('Protected content')).toBeInTheDocument();
  });

  it('redirects to /login when there is no token and no user', () => {
    // Both null → immediate redirect (no refresh attempt)
    useAuthStore.setState({ token: null, user: null });

    // Mock fetch to assert it is NOT called
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    renderProtectedRoute();

    // Children must NOT be shown
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
    // fetch must NOT be called (no refresh when user is absent)
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('renders children after a successful silent refresh (user in store, no token)', async () => {
    // Simulates a page refresh: user persisted to localStorage but token is memory-only
    useAuthStore.setState({ token: null, user: TEST_USER });

    const fetchMock = makeFetchMock(() => ({
      status: 200,
      ok: true,
      json: () => Promise.resolve({ access_token: 'new-token' }),
    }));
    vi.stubGlobal('fetch', fetchMock);

    renderProtectedRoute();

    // During the refresh the component returns null (loading)
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument();

    // After refresh resolves, children are shown
    await screen.findByText('Protected content');
    expect(screen.getByText('Protected content')).toBeInTheDocument();

    // Store should now have the new token
    expect(useAuthStore.getState().token).toBe('new-token');

    // fetch was called with the refresh endpoint
    expect(fetchMock).toHaveBeenCalledWith(REFRESH_URL, { method: 'POST', credentials: 'include' });
  });

  it('redirects to /login when silent refresh returns 401', async () => {
    useAuthStore.setState({ token: null, user: TEST_USER });

    const fetchMock = makeFetchMock(() => ({ status: 401, ok: false }));
    vi.stubGlobal('fetch', fetchMock);

    renderProtectedRoute();

    // Wait for the refresh to complete and the component to settle
    await waitFor(() => {
      expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
    });

    // Store should be cleared (logout was called)
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().token).toBeNull();
  });

  it('redirects to /login when silent refresh returns 403', async () => {
    useAuthStore.setState({ token: null, user: TEST_USER });

    const fetchMock = makeFetchMock(() => ({ status: 403, ok: false }));
    vi.stubGlobal('fetch', fetchMock);

    renderProtectedRoute();

    await waitFor(() => {
      expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
    });

    // 403 also triggers logout
    expect(useAuthStore.getState().user).toBeNull();
  });

  it('redirects to /login on network error without logging out (token stays null, user preserved is NOT required, just no crash)', async () => {
    useAuthStore.setState({ token: null, user: TEST_USER });

    const fetchMock = vi.fn(() => Promise.reject(new Error('Network error')));
    vi.stubGlobal('fetch', fetchMock);

    renderProtectedRoute();

    // After the network error, the component finishes refreshing and token is still null
    // → Navigate to /login is rendered (children not shown)
    await waitFor(() => {
      expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
    });

    // Per the component's catch block: network errors do NOT call logout
    // user may or may not still be in store — the important thing is no crash and no children shown
  });

  it('shows nothing (null) while the refresh is in-flight', async () => {
    useAuthStore.setState({ token: null, user: TEST_USER });

    // Hang the refresh indefinitely
    let resolveRefresh!: (value: unknown) => void;
    const fetchMock = vi.fn(
      () =>
        new Promise((resolve) => {
          resolveRefresh = resolve;
        }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const { container } = renderProtectedRoute();

    // While in-flight: component returns null → nothing rendered
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
    // The container should be essentially empty (null render)
    expect(container.firstChild).toBeNull();

    // Unblock the fetch so subsequent tests start clean
    resolveRefresh({
      status: 200,
      ok: true,
      json: () => Promise.resolve({ access_token: 'tok' }),
    });
  });

  it('does not call fetch when token is already present (no unnecessary refresh)', () => {
    useAuthStore.setState({ token: 'already-valid', user: TEST_USER });

    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    renderProtectedRoute();

    expect(screen.getByText('Protected content')).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('renders children of any type, not just divs', async () => {
    useAuthStore.setState({ token: 'token', user: TEST_USER });

    renderProtectedRoute(<span data-testid="child-span">Hello</span>);

    expect(screen.getByTestId('child-span')).toBeInTheDocument();
  });
});
