import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const setAuth = useAuthStore((s) => s.setAuth);
  const logout = useAuthStore((s) => s.logout);

  // When user is present (from persisted localStorage) but token is null
  // (not persisted — page was refreshed), attempt a silent refresh via the
  // httpOnly cookie before deciding to redirect to login.
  const [isRefreshing, setIsRefreshing] = useState(() => !!user && !token);

  useEffect(() => {
    if (!user || token) {
      setIsRefreshing(false);
      return;
    }
    const apiUrl = import.meta.env.VITE_API_URL as string;
    fetch(`${apiUrl}/auth/refresh`, { method: 'POST', credentials: 'include' })
      .then((r) => {
        if (r.status === 401 || r.status === 403) {
          logout();   // cookie is gone — session is genuinely dead
          return undefined;
        }
        if (!r.ok) {
          // Transient failure (429, 5xx): don't destroy session state.
          // token stays null → Navigate to /login lets the user retry.
          return undefined;
        }
        return r.json() as Promise<{ access_token?: string }>;
      })
      .then((data) => {
        if (data?.access_token && user) {
          setAuth(data.access_token, user);
        }
        // On undefined (transient error or 401/403 already handled): fall through.
        // token stays null, redirect to /login happens after setIsRefreshing(false).
      })
      .catch(() => {
        // Network error: don't logout — let redirect happen, user can retry.
      })
      .finally(() => setIsRefreshing(false));
  }, []); // only on mount

  if (isRefreshing) return null;
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
