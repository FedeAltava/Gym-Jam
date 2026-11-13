import { screen, within } from '@testing-library/react';
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

function makeSession(id: string, workoutName: string, startedAt: Date = new Date(), logs?: unknown[]) {
  return {
    id,
    workout_id: 'w1',
    training_day_id: 'day-today',
    workout_name: workoutName,
    day_of_week: TODAY_KEY,
    started_at: startedAt.toISOString(),
    completed_at: startedAt.toISOString(),
    status: 'completed',
    logs: logs ?? [
      {
        id: `${id}-log1`,
        workout_exercise_id: 'we1',
        exercise_name: 'Press banca',
        muscle_group: 'Pecho',
        set_number: 1,
        reps_completed: 10,
        weight_kg: 80,
      },
    ],
  };
}

const CATALOG = [
  { id: 'bench-press', name: 'Press banca', muscle_group: 'Pecho', is_bodyweight: false },
  { id: 'lat-pulldown', name: 'Jalón al pecho', muscle_group: 'Espalda', is_bodyweight: false },
  { id: 'leg-press', name: 'Prensa', muscle_group: 'Piernas', is_bodyweight: false },
];

function planExercise(id: string, exercise_id: string, sets: number) {
  return { id, exercise_id, order: 1, sets, reps_per_set: 8, weight_kg: null };
}

/** Active workout with two plan days: today and the next weekday. */
const PLANNED_WORKOUT = {
  ...ACTIVE_WORKOUT,
  training_days: [
    {
      id: 'day-today',
      day_of_week: TODAY_KEY,
      order: 0,
      exercises: [planExercise('we1', 'bench-press', 3), planExercise('we2', 'lat-pulldown', 3)],
    },
    {
      id: 'day-next',
      day_of_week: DAYS[(DAYS.indexOf(TODAY_KEY) + 1) % 7],
      order: 1,
      exercises: [planExercise('we3', 'leg-press', 4)],
    },
  ],
};

function daysAgo(days: number): Date {
  return new Date(Date.now() - days * 86_400_000);
}

/** Monday 00:00 UTC of the week `weeksBack` weeks before the current one, as YYYY-MM-DD. */
function mondayUTC(weeksBack: number): string {
  const now = new Date();
  const fromMonday = (now.getUTCDay() + 6) % 7;
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - fromMonday - 7 * weeksBack))
    .toISOString()
    .slice(0, 10);
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
    if (path.startsWith('/exercises')) {
      return Promise.resolve(CATALOG);
    }
    if (path.startsWith('/sessions')) {
      const items = overrides.sessions ?? [makeSession('s1', 'Full Body A'), makeSession('s2', 'Full Body B')];
      return Promise.resolve({ items, total: (items as unknown[]).length, page: 1, page_size: 20 });
    }
    return Promise.resolve(undefined);
  });
}

beforeEach(() => {
  useAuthStore.setState({
    token: 'token',
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

  it('shows the active streak from the stats endpoint in the weekly chart', async () => {
    mockApi();
    renderWithProviders(<DashboardPage />);

    const week = await screen.findByRole('region', { name: 'Esta semana' });
    expect(within(week).getByText('Racha activa')).toBeInTheDocument();
    expect(within(week).getByText('3')).toBeInTheDocument();
    expect(within(week).getByText(/días seguidos/)).toBeInTheDocument();
  });

  it('orders the home: week with streak, sets per muscle, next workout, weekly consistency', async () => {
    mockApi();
    renderWithProviders(<DashboardPage />);

    const week = await screen.findByRole('region', { name: 'Esta semana' });
    const muscles = screen.getByRole('region', { name: 'Series por músculo' });
    const next = screen.getByRole('link', { name: /Empezar sesión/ });
    const consistency = screen.getByRole('region', { name: 'Constancia por semanas' });
    const follows = (a: Node, b: Node) => Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
    expect(follows(week, muscles)).toBe(true);
    expect(follows(muscles, next)).toBe(true);
    expect(follows(next, consistency)).toBe(true);
  });

  it('loads the completed sessions of the last 8 weeks', async () => {
    mockApi();
    renderWithProviders(<DashboardPage />);

    await screen.findByRole('region', { name: 'Constancia por semanas' });
    expect(mockApiFetch).toHaveBeenCalledWith(
      `/sessions?status=completed&date_from=${mondayUTC(7)}&page=1&page_size=100`,
    );
  });

  it('counts this week\'s sets per muscle against the sets planned in the routine', async () => {
    const log = (id: string, muscle_group: string) => ({
      id, workout_exercise_id: 'we1', exercise_name: 'x', muscle_group, set_number: 1, reps_completed: 8, weight_kg: 50,
    });
    mockApi({
      workouts: [PLANNED_WORKOUT],
      sessions: [makeSession('s1', 'Torso', new Date(), [log('l1', 'Pecho'), log('l2', 'Pecho'), log('l3', 'Espalda')])],
    });
    renderWithProviders(<DashboardPage />);

    const muscles = await screen.findByRole('list', { name: 'Series por músculo' });
    expect(within(muscles).getAllByRole('listitem').map((li) => li.getAttribute('aria-label'))).toEqual([
      'Pecho: 2 de 3 series',
      'Espalda: 1 de 3 series',
      'Piernas: 0 de 4 series',
    ]);
  });

  it('shows the sessions of each of the last 8 weeks against the plan days', async () => {
    mockApi({
      workouts: [PLANNED_WORKOUT],
      sessions: [
        makeSession('s1', 'A', new Date()),
        makeSession('s2', 'A', daysAgo(7)),
        makeSession('s3', 'B', daysAgo(7)),
        makeSession('s4', 'A', daysAgo(21)),
      ],
    });
    renderWithProviders(<DashboardPage />);

    const weeks = await screen.findByRole('list', { name: 'Constancia por semanas' });
    const labels = within(weeks).getAllByRole('listitem').map((li) => li.getAttribute('aria-label'));
    expect(labels).toHaveLength(8);
    expect(labels.map((label) => label?.split(': ')[1])).toEqual([
      '0 de 2 sesiones', '0 de 2 sesiones', '0 de 2 sesiones', '0 de 2 sesiones',
      '1 de 2 sesiones', '0 de 2 sesiones', '2 de 2 sesiones', '1 de 2 sesiones',
    ]);
    expect(screen.getByText('1 de 8 semanas completas')).toBeInTheDocument();
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

  it('no longer shows the recent activity list', async () => {
    mockApi();
    renderWithProviders(<DashboardPage />);

    await screen.findByRole('region', { name: 'Esta semana' });
    expect(screen.queryByText('Actividad reciente')).not.toBeInTheDocument();
  });
});
