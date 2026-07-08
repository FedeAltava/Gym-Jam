import { screen } from '@testing-library/react';
import { renderWithProviders } from '../test/test-utils';
import { DashboardPage } from './DashboardPage';
import { useAuthStore } from '../store/authStore';
import { DAYS } from '../lib/days';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../lib/api';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

const TODAY_KEY = DAYS[(new Date().getDay() + 6) % 7];

const STATS_FIXTURE = {
  total_sessions: 12,
  streak: 3,
  total_prs: 5,
  weekly_volume_kg: 1200,
  weekly_sessions: 2,
  weekly_prs: 1,
};

const ZERO_STATS = {
  total_sessions: 0,
  streak: 0,
  total_prs: 0,
  weekly_volume_kg: 0,
  weekly_sessions: 0,
  weekly_prs: 0,
};

const ACTIVE_WORKOUT = {
  id: 'w1',
  name: 'Push Pull Legs',
  description: null,
  is_active: true,
  training_days: [
    { id: 'day-today', day_of_week: TODAY_KEY, order: 0, exercises: [] },
  ],
};

const INACTIVE_WORKOUT = {
  ...ACTIVE_WORKOUT,
  id: 'w2',
  name: 'Rutina Vieja',
  is_active: false,
};

function makeSession(id: string, workoutName: string) {
  return {
    id,
    workout_id: 'w1',
    training_day_id: 'day-today',
    workout_name: workoutName,
    day_of_week: TODAY_KEY,
    started_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
    status: 'completed',
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

interface Overrides {
  stats?: typeof STATS_FIXTURE;
  workouts?: unknown[];
  sessions?: unknown[];
}

function mockApi(overrides: Overrides = {}) {
  mockApiFetch.mockImplementation((path: string) => {
    if (path.startsWith('/users/me/stats')) {
      return Promise.resolve(overrides.stats ?? STATS_FIXTURE);
    }
    if (path.startsWith('/workouts')) {
      return Promise.resolve(overrides.workouts ?? [ACTIVE_WORKOUT]);
    }
    if (path.startsWith('/sessions')) {
      return Promise.resolve(
        overrides.sessions ?? [makeSession('s1', 'Full Body A'), makeSession('s2', 'Full Body B')],
      );
    }
    return Promise.resolve(undefined);
  });
}

beforeEach(() => {
  useAuthStore.setState({
    token: 'token',
    refreshToken: 'refresh',
    user: { id: 'u1', email: 'federico@example.com', created_at: '2026-01-01T00:00:00Z', rest_seconds: 90, units: 'kg' as const },
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('DashboardPage', () => {
  it('renders the greeting with the first name derived from the user email', async () => {
    mockApi();
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText(/Federico/)).toBeInTheDocument();
  });

  it('renders the streak number from the stats endpoint', async () => {
    mockApi();
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText('3')).toBeInTheDocument();
    expect(screen.getByText(/días seguidos/)).toBeInTheDocument();
  });

  it('renders the next workout card with the active workout and a session start link', async () => {
    mockApi();
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText('Push Pull Legs')).toBeInTheDocument();
    const startLink = screen.getByRole('link', { name: /Empezar sesión/ });
    expect(startLink).toHaveAttribute('href', '/workouts/w1/session/day-today');
    // Today is a plan day, so the card must show "Hoy · {DayName}"
    // (distinct from the "Hoy, {date}" greeting subtitle).
    expect(screen.getByText(/Hoy ·/)).toBeInTheDocument();
  });

  it('ignores inactive workouts when resolving the active workout', async () => {
    mockApi({ workouts: [INACTIVE_WORKOUT, ACTIVE_WORKOUT] });
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText('Push Pull Legs')).toBeInTheDocument();
    const startLink = screen.getByRole('link', { name: /Empezar sesión/ });
    expect(startLink).toHaveAttribute('href', '/workouts/w1/session/day-today');
  });

  it('renders the empty state CTA when there is no active workout and no sessions', async () => {
    mockApi({ stats: ZERO_STATS, workouts: [], sessions: [] });
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText(/Crea tu primera rutina/)).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Empezar sesión/ })).not.toBeInTheDocument();
  });

  it('renders at most the last 2 completed sessions in recent activity', async () => {
    mockApi({
      sessions: [
        makeSession('s1', 'Sesión Uno'),
        makeSession('s2', 'Sesión Dos'),
        makeSession('s3', 'Sesión Tres'),
      ],
    });
    renderWithProviders(<DashboardPage />);

    expect(await screen.findByText('Actividad reciente')).toBeInTheDocument();
    expect(screen.getByText('Sesión Uno')).toBeInTheDocument();
    expect(screen.getByText('Sesión Dos')).toBeInTheDocument();
    expect(screen.queryByText('Sesión Tres')).not.toBeInTheDocument();
  });

  it('shows the no-sessions message when the user has an active workout but no completed sessions', async () => {
    mockApi({ sessions: [] });
    renderWithProviders(<DashboardPage />);

    expect(
      await screen.findByText(/Aún no has completado ningún entrenamiento/),
    ).toBeInTheDocument();
  });
});
