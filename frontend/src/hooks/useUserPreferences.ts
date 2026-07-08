import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { UserResponse } from '../types/api';

export interface UserPreferences {
  rest_seconds: number;
  units: 'kg' | 'lb';
}

export function useUserPreferences() {
  return useQuery({
    queryKey: ['user', 'me'],
    queryFn: () => apiFetch<UserPreferences>('/auth/me'),
    staleTime: 5 * 60 * 1000,
  });
}

export interface UpdatePreferencesPayload {
  rest_seconds?: number;
  units?: 'kg' | 'lb';
}

export function useUpdatePreferences() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdatePreferencesPayload) =>
      apiFetch<UserResponse>('/users/me/preferences', {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['user', 'me'] });
    },
  });
}
