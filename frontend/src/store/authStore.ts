import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserResponse } from '../types/api';

const AUTH_STORAGE_KEY = 'auth-storage';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: UserResponse | null;
  setAuth: (token: string, refreshToken: string, user: UserResponse) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      user: null,
      setAuth: (token, refreshToken, user) => set({ token, refreshToken, user }),
      logout: () => set({ token: null, refreshToken: null, user: null }),
    }),
    { name: AUTH_STORAGE_KEY }
  )
);

// Cross-tab sync: when another tab rotates the refresh token (or logs out),
// rehydrate from localStorage so this tab never presents the stale, already
// rotated token (which would look like token reuse to the backend).
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key === AUTH_STORAGE_KEY || event.key === null) {
      void useAuthStore.persist.rehydrate();
    }
  });
}
