import { apiFetch, ApiError } from './api';
import { useAuthStore } from '../store/authStore';

const API_URL = 'http://test.local';

const MOCK_USER = { id: 'u1', email: 'test@example.com', created_at: '2024-01-01T00:00:00Z' };

function makeResponse(status: number, body?: unknown, ok?: boolean): Response {
  const isOk = ok ?? (status >= 200 && status < 300);
  return {
    status,
    ok: isOk,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(JSON.stringify(body)),
  } as unknown as Response;
}

function makeJsonErrorResponse(status: number, body: unknown): Response {
  return makeResponse(status, body, false);
}

function makeNonJsonErrorResponse(status: number): Response {
  return {
    status,
    ok: false,
    json: () => Promise.reject(new SyntaxError('not json')),
    text: () => Promise.resolve('plain text error'),
  } as unknown as Response;
}

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  fetchMock.mockReset();
  useAuthStore.setState({ token: null, refreshToken: null, user: null });
  vi.spyOn(window, 'location', 'get').mockReturnValue({ href: '' } as Location);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  useAuthStore.setState({ token: null, refreshToken: null, user: null });
});

describe('apiFetch happy path', () => {
  it('sends Authorization Bearer header from the auth store token', async () => {
    useAuthStore.setState({ token: 'my-token', refreshToken: 'rt', user: MOCK_USER });
    fetchMock.mockResolvedValueOnce(makeResponse(200, { id: 1 }));

    await apiFetch('/api/test');

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect((options.headers as Record<string, string>)['Authorization']).toBe('Bearer my-token');
  });

  it('sends no Authorization header when store has no token', async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(200, { id: 1 }));

    await apiFetch('/api/test');

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect((options.headers as Record<string, string>)['Authorization']).toBeUndefined();
  });

  it('does not clobber a caller-supplied Authorization header', async () => {
    useAuthStore.setState({ token: 'store-token', refreshToken: 'rt', user: MOCK_USER });
    fetchMock.mockResolvedValueOnce(makeResponse(200, { ok: true }));

    await apiFetch('/api/test', {
      headers: { Authorization: 'Bearer caller-token' },
    });

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect((options.headers as Record<string, string>)['Authorization']).toBe('Bearer caller-token');
  });

  it('returns parsed JSON on 200', async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(200, { name: 'gym' }));

    const result = await apiFetch<{ name: string }>('/api/test');

    expect(result).toEqual({ name: 'gym' });
  });

  it('returns undefined on 204', async () => {
    fetchMock.mockResolvedValueOnce(makeResponse(204, undefined));

    const result = await apiFetch('/api/test', { method: 'DELETE' });

    expect(result).toBeUndefined();
  });
});

describe('apiFetch error mapping', () => {
  it('throws ApiError with body.detail string and status on non-ok response', async () => {
    fetchMock.mockResolvedValueOnce(makeJsonErrorResponse(422, { detail: 'Not found' }));

    await expect(apiFetch('/api/test')).rejects.toSatisfy(
      (err: unknown) => err instanceof ApiError && err.message === 'Not found' && err.status === 422,
    );
  });

  it('joins array detail (FastAPI validation errors) with "; "', async () => {
    fetchMock.mockResolvedValueOnce(
      makeJsonErrorResponse(422, {
        detail: [{ msg: 'field required' }, { msg: 'invalid value' }],
      }),
    );

    await expect(apiFetch('/api/test')).rejects.toSatisfy(
      (err: unknown) =>
        err instanceof ApiError &&
        err.message === 'field required; invalid value' &&
        err.status === 422,
    );
  });

  it('falls back to "Unknown error" when the error body is not JSON', async () => {
    fetchMock.mockResolvedValueOnce(makeNonJsonErrorResponse(500));

    await expect(apiFetch('/api/test')).rejects.toSatisfy(
      (err: unknown) =>
        err instanceof ApiError && err.message === 'Unknown error' && err.status === 500,
    );
  });
});

describe('401 refresh-and-retry', () => {
  it('on 401 with a token, POSTs /auth/refresh, retries the original request with the new access token, and returns its result', async () => {
    useAuthStore.setState({ token: 'old-token', refreshToken: 'old-refresh', user: MOCK_USER });

    fetchMock
      .mockResolvedValueOnce(makeResponse(401, null, false))
      .mockResolvedValueOnce(
        makeResponse(200, { access_token: 'new-token', refresh_token: 'new-refresh', token_type: 'bearer' }),
      )
      .mockResolvedValueOnce(makeResponse(200, { data: 'ok' }));

    const result = await apiFetch<{ data: string }>('/api/test');

    expect(result).toEqual({ data: 'ok' });

    const refreshCall = fetchMock.mock.calls[1] as [string, RequestInit];
    expect(refreshCall[0]).toBe(`${API_URL}/auth/refresh`);
    expect(refreshCall[1].method).toBe('POST');

    const retryCall = fetchMock.mock.calls[2] as [string, RequestInit];
    expect((retryCall[1].headers as Record<string, string>)['Authorization']).toBe('Bearer new-token');
  });

  it('updates the auth store with the rotated access + refresh tokens after a successful refresh', async () => {
    useAuthStore.setState({ token: 'old-token', refreshToken: 'old-refresh', user: MOCK_USER });

    fetchMock
      .mockResolvedValueOnce(makeResponse(401, null, false))
      .mockResolvedValueOnce(
        makeResponse(200, { access_token: 'new-token', refresh_token: 'new-refresh', token_type: 'bearer' }),
      )
      .mockResolvedValueOnce(makeResponse(200, {}));

    await apiFetch('/api/test');

    const state = useAuthStore.getState();
    expect(state.token).toBe('new-token');
    expect(state.refreshToken).toBe('new-refresh');
    expect(state.user).toEqual(MOCK_USER);
  });

  it('when refresh returns 401, clears the auth store and throws ApiError 401', async () => {
    useAuthStore.setState({ token: 'old-token', refreshToken: 'old-refresh', user: MOCK_USER });

    fetchMock
      .mockResolvedValueOnce(makeResponse(401, null, false))
      .mockResolvedValueOnce(makeResponse(401, null, false));

    await expect(apiFetch('/api/test')).rejects.toSatisfy(
      (err: unknown) => err instanceof ApiError && err.status === 401,
    );

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.user).toBeNull();
  });

  it('when refresh returns 500, KEEPS the auth store intact and throws ApiError with status 500', async () => {
    useAuthStore.setState({ token: 'old-token', refreshToken: 'old-refresh', user: MOCK_USER });

    fetchMock
      .mockResolvedValueOnce(makeResponse(401, null, false))
      .mockResolvedValueOnce(makeResponse(500, { detail: 'Server error' }, false));

    await expect(apiFetch('/api/test')).rejects.toSatisfy(
      (err: unknown) => err instanceof ApiError && err.status === 500,
    );

    const state = useAuthStore.getState();
    expect(state.token).toBe('old-token');
    expect(state.refreshToken).toBe('old-refresh');
    expect(state.user).toEqual(MOCK_USER);
  });

  it('when the retried request still returns 401, clears the auth store and throws ApiError 401', async () => {
    useAuthStore.setState({ token: 'old-token', refreshToken: 'old-refresh', user: MOCK_USER });

    fetchMock
      .mockResolvedValueOnce(makeResponse(401, null, false))
      .mockResolvedValueOnce(
        makeResponse(200, { access_token: 'new-token', refresh_token: 'new-refresh', token_type: 'bearer' }),
      )
      .mockResolvedValueOnce(makeResponse(401, null, false));

    await expect(apiFetch('/api/test')).rejects.toSatisfy(
      (err: unknown) => err instanceof ApiError && err.status === 401,
    );

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.user).toBeNull();
  });

  it('does NOT attempt refresh for /auth/login 401', async () => {
    useAuthStore.setState({ token: null, refreshToken: null, user: null });

    fetchMock.mockResolvedValueOnce(makeJsonErrorResponse(401, { detail: 'Invalid credentials' }));

    await expect(apiFetch('/auth/login', { method: 'POST' })).rejects.toSatisfy(
      (err: unknown) => err instanceof ApiError && err.status === 401,
    );

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('single-flight — two concurrent 401 requests trigger exactly one call to /auth/refresh', async () => {
    useAuthStore.setState({ token: 'old-token', refreshToken: 'old-refresh', user: MOCK_USER });

    let refreshResolve!: (r: Response) => void;
    const refreshPending = new Promise<Response>((resolve) => {
      refreshResolve = resolve;
    });

    fetchMock.mockImplementation((url: string) => {
      if (url === `${API_URL}/auth/refresh`) {
        return refreshPending;
      }
      if (url === `${API_URL}/api/test`) {
        if (
          fetchMock.mock.calls
            .slice(0, fetchMock.mock.calls.indexOf(fetchMock.mock.calls.find((c) => c[0] === url && fetchMock.mock.calls.indexOf(c) > 0)!))
            .filter((c) => c[0] === url).length === 0
        ) {
          return Promise.resolve(makeResponse(401, null, false));
        }
        return Promise.resolve(makeResponse(200, { data: 'ok' }));
      }
      return Promise.resolve(makeResponse(200, { data: 'ok' }));
    });

    const [p1, p2] = [apiFetch('/api/test'), apiFetch('/api/test')];

    await Promise.resolve();
    refreshResolve(
      makeResponse(200, { access_token: 'new-token', refresh_token: 'new-refresh', token_type: 'bearer' }),
    );

    await Promise.allSettled([p1, p2]);

    const refreshCalls = fetchMock.mock.calls.filter(
      (c) => (c as [string])[0] === `${API_URL}/auth/refresh`,
    );
    expect(refreshCalls).toHaveLength(1);
  });

  it('does not resurrect a session — if store was logged out while refresh was in flight, throws and leaves store logged out', async () => {
    useAuthStore.setState({ token: 'old-token', refreshToken: 'old-refresh', user: MOCK_USER });

    let refreshResolve!: (r: Response) => void;
    const refreshPending = new Promise<Response>((resolve) => {
      refreshResolve = resolve;
    });

    let firstCall = true;
    fetchMock.mockImplementation((url: string) => {
      if (url === `${API_URL}/auth/refresh`) {
        return refreshPending;
      }
      if (firstCall) {
        firstCall = false;
        return Promise.resolve(makeResponse(401, null, false));
      }
      return Promise.resolve(makeResponse(200, { data: 'ok' }));
    });

    const promise = apiFetch('/api/test');

    await Promise.resolve();
    await Promise.resolve();

    useAuthStore.getState().logout();

    refreshResolve(
      makeResponse(200, { access_token: 'new-token', refresh_token: 'new-refresh', token_type: 'bearer' }),
    );

    await expect(promise).rejects.toSatisfy(
      (err: unknown) => err instanceof ApiError && err.status === 401,
    );

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.user).toBeNull();
  });
});
