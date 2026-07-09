import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserResponse } from '../types/api';

const AUTH_STORAGE_KEY = 'auth-storage';

interface AuthState {
  token: string | null;
  user: UserResponse | null;
  setAuth: (token: string, user: UserResponse) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    {
      name: AUTH_STORAGE_KEY,
      // Only persist user identity — the access token lives in memory only.
      // The httpOnly refresh cookie handles silent re-auth after page reload.
      partialize: (state) => ({ user: state.user }),
    }
  )
);

// Cross-tab sync: when another tab logs out (clears user from localStorage),
// rehydrate so this tab redirects to login.
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key === AUTH_STORAGE_KEY || event.key === null) {
      void useAuthStore.persist.rehydrate();
    }
  });
}
