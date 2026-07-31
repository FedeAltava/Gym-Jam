import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../lib/api';
import { queryClient } from '../lib/queryClient';
import { useAuthStore } from '../store/authStore';
import type { TokenResponse, UserResponse } from '../types/api';

interface ForgotPasswordPayload { email: string; }
interface ResetPasswordPayload { token: string; new_password: string; }

interface LoginPayload { email: string; password: string; }
interface RegisterPayload { email: string; password: string; }

export function useLoginMutation() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (data: LoginPayload) => {
      const token = await apiFetch<TokenResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      const user = await apiFetch<UserResponse>('/auth/me', {
        headers: { Authorization: `Bearer ${token.access_token}` },
      });
      return { token, user };
    },
    onSuccess: ({ token, user }) => {
      // Clear any previous user's cached data before loading the new session
      // so no data bleeds across users on a shared device.
      queryClient.clear();
      setAuth(token.access_token, user);
      navigate('/dashboard');
    },
  });
}

export function useRegisterMutation() {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: RegisterPayload) =>
      apiFetch<UserResponse>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => navigate('/login'),
  });
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: () => apiFetch<void>('/auth/logout', { method: 'POST' }),
    onSettled: () => {
      // Clear auth store and redirect regardless of API success/failure
      logout();
      // Clear React Query cache so the next user cannot see this user's
      // cached workouts, sessions, or stats on a shared device.
      queryClient.clear();
      navigate('/login');
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (data: ForgotPasswordPayload) =>
      apiFetch<void>('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (data: ResetPasswordPayload) =>
      apiFetch<void>('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  });
}
