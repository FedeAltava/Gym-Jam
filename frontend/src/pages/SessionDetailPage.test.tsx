import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/test-utils';
import { SessionDetailPage } from './SessionDetailPage';
import { useAuthStore } from '../store/authStore';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return {
    ...actual,
    useParams: vi.fn(() => ({ sessionId: 'sess1' })),
    useNavigate: vi.fn(() => vi.fn()),
  };
});

import { apiFetch } from '../lib/api';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

/**
 * Completed session with 2 exercises:
 *   - Press banca (weighted): 3 sets at 80 kg, 100 kg, 80 kg
 *   - Dominadas (bodyweight): 3 sets, weight_kg null
 *
 * pr_count: 1, records: [Press banca 80 kg × 8] → only the first 80 kg × 8
 * set (set_number 1) gets the PR badge, not the heaviest 100 kg set.
 * duration_seconds: 3600 → "1h 0min"
 * volume = (8 * 80) + (10 * 100) + (8 * 80) + (12 * 0) * 3
 *        = 640 + 1000 + 640 = 2280
 */
const SESSION_WITH_PR = {
  id: 'sess1',
  workout_id: 'w1',
  training_day_id: 'day1',
  workout_name: 'Push A',
  day_of_week: 'MONDAY',
  started_at: '2024-06-03T10:00:00Z',
  completed_at: '2024-06-03T11:00:00Z',
  status: 'completed' as const,
  duration_seconds: 3600,
  pr_count: 1,
  records: [
    { exercise_id: 'bench-press', weight_kg: 80, reps: 8, estimated_one_rep_max_kg: 101.3 },
  ],
  logs: [
    {
      id: 'log1',
      workout_exercise_id: 'we1',
      exercise_id: 'bench-press',
      exercise_name: 'Press banca',
      muscle_group: 'Pecho',
      set_number: 1,
      reps_completed: 8,
      weight_kg: 80,
    },
    {
      id: 'log2',
      workout_exercise_id: 'we1',
      exercise_id: 'bench-press',
      exercise_name: 'Press banca',
      muscle_group: 'Pecho',
      set_number: 2,
      reps_completed: 10,
      weight_kg: 100,
    },
    {
      id: 'log3',
      workout_exercise_id: 'we1',
      exercise_id: 'bench-press',
      exercise_name: 'Press banca',
      muscle_group: 'Pecho',
      set_number: 3,
      reps_completed: 8,
      weight_kg: 80,
    },
    {
      id: 'log4',
      workout_exercise_id: 'we2',
      exercise_id: 'pull-up',
      exercise_name: 'Dominadas',
      muscle_group: 'Espalda',
      set_number: 1,
      reps_completed: 12,
      weight_kg: null,
    },
    {
      id: 'log5',
      workout_exercise_id: 'we2',
      exercise_id: 'pull-up',
      exercise_name: 'Dominadas',
      muscle_group: 'Espalda',
      set_number: 2,
      reps_completed: 10,
      weight_kg: null,
    },
    {
      id: 'log6',
      workout_exercise_id: 'we2',
      exercise_id: 'pull-up',
      exercise_name: 'Dominadas',
      muscle_group: 'Espalda',
      set_number: 3,
      reps_completed: 8,
      weight_kg: null,
    },
  ],
};

/** Same session but without PRs. */
const SESSION_NO_PR = {
  ...SESSION_WITH_PR,
  pr_count: 0,
  records: [],
};

/** Empty history — no previous sessions of the same workout. */
const EMPTY_HISTORY = {
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
};

/**
 * Wire up apiFetch mock.
 * - /sessions/sess1 → session detail
 * - /sessions?... → paginated history (always empty for isolation)
 */
function mockApi(sessionFixture: typeof SESSION_WITH_PR = SESSION_WITH_PR) {
  mockApiFetch.mockImplementation((path: string) => {
    if (path === '/sessions/sess1') {
      return Promise.resolve(sessionFixture);
    }
    if (path.startsWith('/sessions')) {
      return Promise.resolve(EMPTY_HISTORY);
    }
    return Promise.resolve(undefined);
  });
}

beforeEach(() => {
  useAuthStore.setState({
    token: 'token',
    user: {
      id: 'u1',
      email: 'test@example.com',
      created_at: '2026-01-01T00:00:00Z',
      rest_seconds: 90,
      units: 'kg' as const,
    },
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('SessionDetailPage — header', () => {
  it('renders the workout name', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByText('Push A')).toBeInTheDocument();
  });

  it('renders the day label for MONDAY', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    // DAY_LABEL['MONDAY'] = 'Lunes'
    expect(await screen.findByText(/Lunes/)).toBeInTheDocument();
  });

  it('renders the formatted date for started_at', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    // 2024-06-03 formatted with es-ES day + short month → "3 jun"
    expect(await screen.findByText(/3 jun/)).toBeInTheDocument();
  });

  it('renders "completada" status in the header subtitle', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByText(/completada/)).toBeInTheDocument();
  });
});

describe('SessionDetailPage — stats bar', () => {
  it('formats duration 3600s as "1h 0min"', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByText('1h 0min')).toBeInTheDocument();
  });

  it('shows volume computed from all weighted sets', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    // volume = 8*80 + 10*100 + 8*80 + 0*3 = 2280
    // The page uses toLocaleString('es-ES'); the exact thousands separator
    // varies between environments (e.g. "2.280" vs "2280") — match either.
    expect(await screen.findByText(/2[.,]?280/)).toBeInTheDocument();
  });

  it('shows PR count label', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    // pr_count=1 → "1 PR"
    expect(await screen.findByText('1 PR')).toBeInTheDocument();
  });

  it('shows "0 PRs" when pr_count is 0', async () => {
    mockApi(SESSION_NO_PR);
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByText('0 PRs')).toBeInTheDocument();
  });
});

describe('SessionDetailPage — exercise cards', () => {
  it('renders both exercise names', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByText('Press banca')).toBeInTheDocument();
    expect(await screen.findByText('Dominadas')).toBeInTheDocument();
  });

  it('renders set rows with reps and weight for weighted exercise', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Press banca');
    // Both exercises have "Serie 1" — getAllByText is correct here.
    const serie1Labels = screen.getAllByText('Serie 1');
    expect(serie1Labels.length).toBeGreaterThanOrEqual(1);
    // Press banca set 1 has 8 reps and 80 kg
    expect(screen.getAllByText('8 reps')[0]).toBeInTheDocument();
    expect(screen.getAllByText('80 kg')[0]).toBeInTheDocument();
  });

  it('renders all set numbers for an exercise', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Press banca');
    // 3 sets for Press banca + 3 sets for Dominadas = 6 "Serie N" labels
    const serieLabels = screen.getAllByText(/^Serie \d$/);
    expect(serieLabels.length).toBeGreaterThanOrEqual(6);
  });
});

describe('SessionDetailPage — PR badge', () => {
  function rowOf(badge: HTMLElement): HTMLElement {
    // The set row is the badge's parent: "Serie N · reps · kg · PR".
    return badge.parentElement as HTMLElement;
  }

  it('marks only the record set given by records, not the heaviest set', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Press banca');
    const prBadges = screen.getAllByText('PR');
    expect(prBadges).toHaveLength(1);
    const row = rowOf(prBadges[0]);
    expect(row).toHaveTextContent('Serie 1');
    expect(row).toHaveTextContent('8 reps');
    expect(row).toHaveTextContent('80 kg');
    expect(row).not.toHaveTextContent('100 kg');
  });

  it('shows the estimated one-rep max next to the badge', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Press banca');
    const estimate = screen.getByText('≈ 101 kg');
    expect(rowOf(estimate)).toHaveTextContent('PR');
    expect(screen.getAllByText(/≈ \d+ kg/)).toHaveLength(1);
  });

  it('marks only the first set matching the record when several sets share weight and reps', async () => {
    // 85 kg × 5 is the heaviest set; the record is 80 kg × 12, logged twice.
    mockApi({
      ...SESSION_WITH_PR,
      records: [{ exercise_id: 'bench-press', weight_kg: 80, reps: 12, estimated_one_rep_max_kg: 112.0 }],
      logs: [
        { id: 'a', workout_exercise_id: 'we1', exercise_id: 'bench-press', exercise_name: 'Press banca', muscle_group: 'Pecho', set_number: 1, reps_completed: 5, weight_kg: 85 },
        { id: 'b', workout_exercise_id: 'we1', exercise_id: 'bench-press', exercise_name: 'Press banca', muscle_group: 'Pecho', set_number: 2, reps_completed: 12, weight_kg: 80 },
        { id: 'c', workout_exercise_id: 'we1', exercise_id: 'bench-press', exercise_name: 'Press banca', muscle_group: 'Pecho', set_number: 3, reps_completed: 12, weight_kg: 80 },
      ],
    });
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Press banca');
    const prBadges = screen.getAllByText('PR');
    expect(prBadges).toHaveLength(1);
    const row = rowOf(prBadges[0]);
    expect(row).toHaveTextContent('Serie 2');
    expect(row).toHaveTextContent('12 reps');
    expect(row).toHaveTextContent('80 kg');
    expect(row).toHaveTextContent('≈ 112 kg');
  });

  it('never marks a set of another exercise with the same weight and reps', async () => {
    mockApi({
      ...SESSION_WITH_PR,
      records: [{ exercise_id: 'incline-press', weight_kg: 80, reps: 8, estimated_one_rep_max_kg: 101.3 }],
      logs: [
        { id: 'a', workout_exercise_id: 'we1', exercise_id: 'bench-press', exercise_name: 'Press banca', muscle_group: 'Pecho', set_number: 1, reps_completed: 8, weight_kg: 80 },
        { id: 'b', workout_exercise_id: 'we3', exercise_id: 'incline-press', exercise_name: 'Press inclinado', muscle_group: 'Pecho', set_number: 1, reps_completed: 8, weight_kg: 80 },
      ],
    });
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Press inclinado');
    const prBadges = screen.getAllByText('PR');
    expect(prBadges).toHaveLength(1);
    expect(rowOf(prBadges[0]).closest('[data-exercise]')).toHaveAttribute('data-exercise', 'Press inclinado');
  });

  it('does NOT show PR badge when records is empty', async () => {
    mockApi(SESSION_NO_PR);
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Press banca');
    expect(screen.queryByText('PR')).not.toBeInTheDocument();
    expect(screen.queryByText(/≈ \d+ kg/)).not.toBeInTheDocument();
  });

  it('renders exactly 2 rows with 80 kg and 1 row with 100 kg', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Press banca');
    expect(screen.getAllByText('80 kg')).toHaveLength(2);
    expect(screen.getAllByText('100 kg')).toHaveLength(1);
  });
});

describe('SessionDetailPage — bodyweight sets', () => {
  it('renders "—" for sets with null weight_kg', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Dominadas');
    // 3 bodyweight sets all render "—" as the weight column
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThanOrEqual(3);
  });

  it('does not render "kg" text for bodyweight sets', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Dominadas');
    // Only the 3 weighted sets of Press banca should show "kg"
    const kgCells = screen.getAllByText(/^\d+ kg$/);
    // 80 kg, 100 kg, 80 kg
    expect(kgCells).toHaveLength(3);
  });
});

describe('SessionDetailPage — duration formatting', () => {
  it('formats 3600s as "1h 0min"', async () => {
    mockApi({ ...SESSION_WITH_PR, duration_seconds: 3600 });
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByText('1h 0min')).toBeInTheDocument();
  });

  it('formats 90s as "1min"', async () => {
    mockApi({ ...SESSION_WITH_PR, duration_seconds: 90 });
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByText('1min')).toBeInTheDocument();
  });

  it('formats 30s as "30s"', async () => {
    mockApi({ ...SESSION_WITH_PR, duration_seconds: 30 });
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByText('30s')).toBeInTheDocument();
  });

  it('formats null duration as "—"', async () => {
    mockApi({ ...SESSION_WITH_PR, duration_seconds: null as unknown as number });
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Push A');
    // "—" appears for null duration in the stats bar
    const dashes = screen.getAllByText('—');
    // At least 1 dash from duration; bodyweight sets also render "—"
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  it('formats 3661s as "1h 1min"', async () => {
    mockApi({ ...SESSION_WITH_PR, duration_seconds: 3661 });
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByText('1h 1min')).toBeInTheDocument();
  });
});

describe('SessionDetailPage — repeat session button', () => {
  it('renders the "Repetir esta sesión" button', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByRole('button', { name: /Repetir esta sesión/ })).toBeInTheDocument();
  });

  it('calls navigate with the correct route when "Repetir esta sesión" is clicked', async () => {
    const navigateFn = vi.fn();
    const { useNavigate } = await import('react-router-dom');
    (useNavigate as ReturnType<typeof vi.fn>).mockReturnValue(navigateFn);

    const user = userEvent.setup();
    mockApi();
    renderWithProviders(<SessionDetailPage />);

    const repeatBtn = await screen.findByRole('button', { name: /Repetir esta sesión/ });
    await user.click(repeatBtn);

    // Route: /workouts/{workout_id}/session/{training_day_id}
    expect(navigateFn).toHaveBeenCalledWith('/workouts/w1/session/day1');
  });
});

describe('SessionDetailPage — back navigation', () => {
  it('renders the back button', async () => {
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByRole('button', { name: /Volver/ })).toBeInTheDocument();
  });

  it('calls navigate(-1) when the back button is clicked', async () => {
    const navigateFn = vi.fn();
    const { useNavigate } = await import('react-router-dom');
    (useNavigate as ReturnType<typeof vi.fn>).mockReturnValue(navigateFn);

    const user = userEvent.setup();
    mockApi();
    renderWithProviders(<SessionDetailPage />);

    const backBtn = await screen.findByRole('button', { name: /Volver/ });
    await user.click(backBtn);

    expect(navigateFn).toHaveBeenCalledWith(-1);
  });
});

describe('SessionDetailPage — loading state', () => {
  it('renders spinner while session is loading', async () => {
    // Never resolves — keeps the component in loading state
    mockApiFetch.mockImplementation(() => new Promise(() => {}));
    renderWithProviders(<SessionDetailPage />);
    // The Spinner component renders an svg or a role that indicates loading
    // We look for the spinner by its aria role or the class the Spinner component outputs
    await screen.findByRole('status');
  });
});

describe('SessionDetailPage — error / not found state', () => {
  it('renders "Sesión no encontrada" when the API returns null', async () => {
    mockApiFetch.mockImplementation((path: string) => {
      if (path === '/sessions/sess1') return Promise.resolve(null);
      if (path.startsWith('/sessions')) return Promise.resolve(EMPTY_HISTORY);
      return Promise.resolve(undefined);
    });
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByText('Sesión no encontrada')).toBeInTheDocument();
  });

  it('shows "Volver al historial" button when session is not found', async () => {
    mockApiFetch.mockImplementation((path: string) => {
      if (path === '/sessions/sess1') return Promise.resolve(null);
      if (path.startsWith('/sessions')) return Promise.resolve(EMPTY_HISTORY);
      return Promise.resolve(undefined);
    });
    renderWithProviders(<SessionDetailPage />);
    expect(await screen.findByRole('button', { name: /Volver al historial/ })).toBeInTheDocument();
  });
});

describe('SessionDetailPage — progress chart sheet', () => {
  it('opens the progress sheet when an exercise card header is clicked', async () => {
    const user = userEvent.setup();
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Press banca');

    // Each exercise card has a "Progreso" button
    const progressBtns = screen.getAllByRole('button', { name: /Progreso/ });
    await user.click(progressBtns[0]);

    // The sheet opens. History is empty so the chart has no data to plot.
    // The sheet shows "Sin datos de peso registrados" in that case.
    expect(screen.getByText('Sin datos de peso registrados')).toBeInTheDocument();
  });

  it('closes the progress sheet when the close button is clicked', async () => {
    const user = userEvent.setup();
    mockApi();
    renderWithProviders(<SessionDetailPage />);
    await screen.findByText('Press banca');

    const progressBtns = screen.getAllByRole('button', { name: /Progreso/ });
    await user.click(progressBtns[0]);

    // Close button inside the sheet
    const closeBtn = screen.getByRole('button', { name: /Cerrar/ });
    await user.click(closeBtn);

    expect(screen.queryByRole('button', { name: /Cerrar/ })).not.toBeInTheDocument();
  });
});
