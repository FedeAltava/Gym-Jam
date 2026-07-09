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
        if (!r.ok) {
          logout();
          return;
        }
        return r.json();
      })
      .then((data?: { access_token?: string }) => {
        if (data?.access_token && user) {
          setAuth(data.access_token, user);
        } else {
          logout();
        }
      })
      .catch(() => logout())
      .finally(() => setIsRefreshing(false));
  }, []); // only on mount

  if (isRefreshing) return null;
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
