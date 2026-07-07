import { useInfiniteQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { SessionHistoryItemResponse } from '../types/api';

const PAGE_SIZE = 20;

interface SessionHistoryFilters {
  workoutId?: string;
  status?: string;
}

function buildQueryString(filters: SessionHistoryFilters): string {
  const params = new URLSearchParams();
  if (filters.workoutId) params.set('workout_id', filters.workoutId);
  if (filters.status) params.set('status', filters.status);
  return params.toString() ? '?' + params.toString() : '';
}

export function useSessionHistory(filters: SessionHistoryFilters = {}) {
  return useInfiniteQuery({
    queryKey: ['sessions', 'history', filters],
    queryFn: ({ pageParam }: { pageParam: number }) => {
      const base = buildQueryString(filters);
      const sep = base ? '&' : '?';
      return apiFetch<SessionHistoryItemResponse[]>(
        `/sessions${base}${sep}limit=${PAGE_SIZE}&offset=${pageParam}`,
      );
    },
    initialPageParam: 0,
    getNextPageParam: (
      lastPage: SessionHistoryItemResponse[],
      allPages: SessionHistoryItemResponse[][],
    ) => (lastPage.length === PAGE_SIZE ? allPages.length * PAGE_SIZE : undefined),
  });
}
