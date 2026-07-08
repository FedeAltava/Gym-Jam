import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/test-utils';
import { HistoryPage } from './HistoryPage';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../lib/api';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeSession(id: string, prCount = 0, durationSeconds: number | null = null) {
  return {
    id,
    workout_id: 'w1',
    training_day_id: 'day-1',
    workout_name: 'Push A',
    day_of_week: 'MONDAY',
    started_at: '2024-06-03T10:00:00Z',
    completed_at: durationSeconds !== null ? '2024-06-03T11:00:00Z' : null,
    status: 'completed' as const,
    duration_seconds: durationSeconds,
    pr_count: prCount,
    logs: [
      {
        id: `${id}-log1`,
        workout_exercise_id: 'we1',
        exercise_name: 'Press banca',
        set_number: 1,
        reps_completed: 10,
        weight_kg: 80,
      },
    ],
  };
}

afterEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('HistoryPage', () => {
  it('renders "Todas" and "Esta semana" filter chips', async () => {
    mockApiFetch.mockResolvedValue([makeSession('s1')]);
    renderWithProviders(<HistoryPage />);

    expect(await screen.findByRole('button', { name: 'Todas' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Esta semana' })).toBeInTheDocument();
  });

  it('clicking "Esta semana" adds date_from to the API call (not period=this_week)', async () => {
    const user = userEvent.setup();
    mockApiFetch.mockResolvedValue([makeSession('s1')]);
    renderWithProviders(<HistoryPage />);

    expect(await screen.findByRole('button', { name: 'Esta semana' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Esta semana' }));

    // All subsequent calls should include date_from= and NOT period=
    const calls = mockApiFetch.mock.calls.map((c) => c[0] as string);
    const weekCall = calls.find((url) => url.includes('date_from='));
    expect(weekCall).toBeDefined();
    expect(weekCall).not.toContain('period=');
    // date_from must be a YYYY-MM-DD ISO date string (Monday of current week)
    expect(weekCall).toMatch(/date_from=\d{4}-\d{2}-\d{2}/);
  });

  it('renders the PR badge when pr_count > 0', async () => {
    mockApiFetch.mockResolvedValue([makeSession('s1', 2, 3600)]);
    renderWithProviders(<HistoryPage />);

    // Wait for the session card
    expect(await screen.findByText('Push A')).toBeInTheDocument();
    expect(screen.getByText('PR')).toBeInTheDocument();
  });

  it('does NOT render the PR badge when pr_count = 0', async () => {
    mockApiFetch.mockResolvedValue([makeSession('s1', 0, 3600)]);
    renderWithProviders(<HistoryPage />);

    expect(await screen.findByText('Push A')).toBeInTheDocument();
    expect(screen.queryByText('PR')).not.toBeInTheDocument();
  });

  it('renders exercise name chips from session logs', async () => {
    mockApiFetch.mockResolvedValue([makeSession('s1')]);
    renderWithProviders(<HistoryPage />);

    expect(await screen.findByText('Press banca')).toBeInTheDocument();
  });

  it('renders formatted duration when duration_seconds is provided', async () => {
    mockApiFetch.mockResolvedValue([makeSession('s1', 0, 3660)]); // 1h 1min
    renderWithProviders(<HistoryPage />);

    expect(await screen.findByText(/1h 1min/)).toBeInTheDocument();
  });
});
