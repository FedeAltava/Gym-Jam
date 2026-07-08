import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';

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
