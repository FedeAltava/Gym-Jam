import type { TokenResponse } from '../types/api';

if (!import.meta.env.VITE_API_URL) {
  throw new Error('VITE_API_URL is not configured');
}

const API_URL = import.meta.env.VITE_API_URL as string;

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function getAuthStore() {
  // Imported lazily inside the function to avoid any potential circular
  // dependency if authStore ever imports from api.ts in the future.
  return import('../store/authStore').then((m) => m.useAuthStore);
}

// Thrown only when /auth/refresh definitively rejects the session (401/403)
// or there is no session to refresh — the ONLY cases that destroy auth state.
class SessionExpiredError extends Error {
  constructor() {
    super('Session expired');
    this.name = 'SessionExpiredError';
  }
}

// Auth endpoints where a 401 means "bad credentials / invalid refresh token",
// not "expired session" — never trigger the refresh-and-retry flow for them.
// /auth/logout is included: refreshing during logout would rotate the refresh
// token and then revoke nothing (the captured token is already stale).
function isAuthExemptPath(path: string): boolean {
  return (
    path.startsWith('/auth/login') ||
    path.startsWith('/auth/refresh') ||
    path.startsWith('/auth/logout')
  );
}

// Single-flight refresh: parallel 401s share one in-flight refresh call
// instead of stampeding /auth/refresh (rotation would revoke everything).
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const useAuthStore = await getAuthStore();
  const { refreshToken, user } = useAuthStore.getState();
  if (!refreshToken || !user) throw new SessionExpiredError();

  // Network errors propagate as-is: they are transient, not session death.
  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (response.status === 401 || response.status === 403) {
    throw new SessionExpiredError();
  }
  if (!response.ok) {
    // 429 / 5xx — retryable failure, must NOT clear auth state.
    throw new ApiError('Session refresh failed', response.status);
  }
  const tokens = (await response.json()) as TokenResponse;
  // The store may have changed while the refresh was in flight: a logout must
  // NOT be resurrected by a late refresh result, and if another tab already
  // rotated the session its (newer) tokens win over ours.
  const current = useAuthStore.getState();
  if (current.refreshToken !== refreshToken) {
    if (current.token && current.refreshToken && current.user) {
      return current.token;
    }
    throw new SessionExpiredError();
  }
  useAuthStore.getState().setAuth(tokens.access_token, tokens.refresh_token, user);
  return tokens.access_token;
}

function getRefreshedToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

function doFetch(
  path: string,
  options: RequestInit,
  token: string | null,
): Promise<Response> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) ?? {}),
  };
  // Never clobber a caller-supplied Authorization header with the store token.
  const hasAuthHeader = Object.keys(headers).some(
    (key) => key.toLowerCase() === 'authorization',
  );
  if (token && !hasAuthHeader) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return fetch(`${API_URL}${path}`, { ...options, headers });
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const useAuthStore = await getAuthStore();
  const token = useAuthStore.getState().token;

  let response = await doFetch(path, options, token);

  if (response.status === 401 && !isAuthExemptPath(path)) {
    // Only authenticated requests get one refresh-and-retry attempt.
    if (token) {
      let newToken: string;
      try {
        newToken = await getRefreshedToken();
      } catch (err) {
        if (err instanceof SessionExpiredError) {
          useAuthStore.getState().logout();
          window.location.href = '/login';
          throw new ApiError('Unauthorized', 401);
        }
        // Transient refresh failure (network, 429, 5xx) — keep the session
        // and surface it to the caller as a normal failed request.
        throw err;
      }
      response = await doFetch(path, options, newToken);
    }
    if (response.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
      throw new ApiError('Unauthorized', 401);
    }
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(body.detail ?? 'Request failed', response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
