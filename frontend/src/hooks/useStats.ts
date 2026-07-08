import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { UserStats } from '../types/api';

export function useUserStats() {
  return useQuery({
    queryKey: ['user-stats'],
    queryFn: () => apiFetch<UserStats>('/users/me/stats'),
  });
}
