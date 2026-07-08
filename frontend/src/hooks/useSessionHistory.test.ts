import { renderHook, waitFor } from '@testing-library/react';
import { apiFetch } from '../lib/api';
import { createWrapper } from '../test/test-utils';
import { useSessionHistory } from './useSessionHistory';
import type { SessionHistoryItemResponse } from '../types/api';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

afterEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeSession(id: string): SessionHistoryItemResponse {
  return {
    id,
    workout_id: 'wk-1',
    training_day_id: 'day-1',
    workout_name: 'Push A',
    day_of_week: 'MONDAY',
    started_at: '2024-01-01T10:00:00Z',
    completed_at: '2024-01-01T11:00:00Z',
    status: 'completed',
    duration_seconds: 3600,
    pr_count: 0,
    logs: [],
  };
}

function makePage(count: number, startIndex = 0): SessionHistoryItemResponse[] {
  return Array.from({ length: count }, (_, i) =>
    makeSession(`sess-${startIndex + i}`),
  );
}

// ---------------------------------------------------------------------------
// useSessionHistory
// ---------------------------------------------------------------------------

describe('useSessionHistory', () => {
  it('calls GET /sessions with no query params when no filters are set', async () => {
    vi.mocked(apiFetch).mockResolvedValue([]);
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSessionHistory(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/sessions?limit=20&offset=0',
    );
  });

  it('includes status query param when status filter is set', async () => {
    vi.mocked(apiFetch).mockResolvedValue([]);
    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useSessionHistory({ status: 'completed' }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      '/sessions?status=completed&limit=20&offset=0',
    );
  });

  it('includes date_from for Monday UTC when period=this_week', async () => {
    vi.mocked(apiFetch).mockResolvedValue([]);
    const { wrapper } = createWrapper();
    const { result } = renderHook(
      () => useSessionHistory({ period: 'this_week' }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const call = vi.mocked(apiFetch).mock.calls[0][0] as string;
    expect(call).toMatch(/date_from=\d{4}-\d{2}-\d{2}/);
    expect(call).not.toContain('period=');
  });

  it('sets hasNextPage to true when a full page (20 items) is returned', async () => {
    vi.mocked(apiFetch).mockResolvedValue(makePage(20));
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSessionHistory(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.hasNextPage).toBe(true);
  });

  it('sets hasNextPage to false for a partial page (fewer than 20 items)', async () => {
    vi.mocked(apiFetch).mockResolvedValue(makePage(7));
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSessionHistory(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.hasNextPage).toBe(false);
  });

  it('sets hasNextPage to false for an empty page', async () => {
    vi.mocked(apiFetch).mockResolvedValue([]);
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useSessionHistory(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.hasNextPage).toBe(false);
  });
});
