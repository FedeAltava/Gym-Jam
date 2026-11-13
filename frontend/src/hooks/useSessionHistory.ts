import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { SessionHistoryItemResponse, SessionHistoryResponse } from '../types/api';

const PAGE_SIZE = 20;

/** Return the ISO-date string for Monday 00:00:00 UTC of the current week. */
function getMondayUTC(): string {
  const now = new Date();
  const dayOfWeek = now.getUTCDay(); // 0 = Sunday … 6 = Saturday
  const daysFromMonday = (dayOfWeek + 6) % 7; // Mon=0 … Sun=6
  const monday = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - daysFromMonday),
  );
  return monday.toISOString().split('T')[0]; // "YYYY-MM-DD"
}

export interface SessionHistoryFilters {
  /** Internal use: dashboard passes 'completed' to show only finished sessions. */
  status?: string;
  /** Page-level filter: 'this_week' maps client-side to date_from=<Monday UTC ISO>. */
  period?: 'this_week';
}

function buildQueryString(filters: SessionHistoryFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set('status', filters.status);
  if (filters.period === 'this_week') params.set('date_from', getMondayUTC());
  return params.toString() ? '?' + params.toString() : '';
}

export function useSessionHistory(filters: SessionHistoryFilters = {}) {
  return useInfiniteQuery({
    queryKey: ['sessions', 'history', filters],
    queryFn: ({ pageParam }: { pageParam: number }) => {
      const base = buildQueryString(filters);
      const sep = base ? '&' : '?';
      return apiFetch<SessionHistoryResponse>(
        `/sessions${base}${sep}page=${pageParam}&page_size=${PAGE_SIZE}`,
      );
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage: SessionHistoryResponse) =>
      lastPage.items.length === PAGE_SIZE ? lastPage.page + 1 : undefined,
  });
}

/**
 * Completed sessions started on or after `dateFrom` (YYYY-MM-DD, UTC day), in
 * one request: the dashboard needs whole weeks, not the paginated list.
 * Keyed under ['sessions', 'history'] so session mutations refresh it.
 */
export function useCompletedSessionsSince(dateFrom: string) {
  return useQuery({
    queryKey: ['sessions', 'history', 'completed-since', dateFrom],
    queryFn: () =>
      apiFetch<SessionHistoryResponse>(
        `/sessions?status=completed&date_from=${dateFrom}&page=1&page_size=100`,
      ),
  });
}

/**
 * Fetch a single session by id directly from the backend.
 *
 * The detail page can be reached for any session, including ones older than
 * the first history page — so it must NOT rely on the paginated history list
 * to resolve the session.
 */
export function useSessionDetail(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['sessions', 'detail', sessionId],
    queryFn: () =>
      apiFetch<SessionHistoryItemResponse>(`/sessions/${sessionId}`),
    enabled: sessionId !== undefined,
  });
}
