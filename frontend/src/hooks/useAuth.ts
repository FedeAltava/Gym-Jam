import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../lib/api';
import { useAuthStore } from '../store/authStore';
import type { TokenResponse, UserResponse } from '../types/api';

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
