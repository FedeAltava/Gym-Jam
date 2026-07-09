import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/test-utils';
import { WorkoutSessionPage } from './WorkoutSessionPage';
import { useAuthStore } from '../store/authStore';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

// Control URL params from tests
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return {
    ...actual,
    useParams: vi.fn(() => ({ workoutId: 'w1', dayId: 'day1' })),
    useNavigate: vi.fn(() => vi.fn()),
  };
});

import { apiFetch } from '../lib/api';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

// started_at exactly 75 seconds ago
const STARTED_AT = new Date(Date.now() - 75_000).toISOString();

const WORKOUT_FIXTURE = {
  id: 'w1',
  name: 'Push Pull Legs',
  description: null,
  is_active: true,
  training_days: [
    {
      id: 'day1',
      day_of_week: 'monday',
      order: 0,
      exercises: [
        // Non-bodyweight exercise — has a weight stepper
        {
          id: 'we1',
          exercise_id: 'e1',
          order: 1,
          sets: 3,
          reps_per_set: 10,
          weight_kg: 80,
        },
        // Bodyweight exercise — no weight stepper
        {
          id: 'we2',
          exercise_id: 'e2',
          order: 2,
          sets: 2,
          reps_per_set: 12,
          weight_kg: null,
        },
      ],
    },
  ],
};

const SESSION_FIXTURE = {
  id: 'sess1',
  workout_id: 'w1',
  training_day_id: 'day1',
  started_at: STARTED_AT,
  status: 'in_progress',
  completed_at: null,
  logs: [],
};

const EXERCISES_FIXTURE = [
  { id: 'e1', name: 'Press banca', muscle_group: 'Pecho', is_bodyweight: false },
  { id: 'e2', name: 'Dominadas', muscle_group: 'Espalda', is_bodyweight: true },
];

const PREFS_FIXTURE = {
  id: 'u1',
  email: 'test@example.com',
  created_at: '2026-01-01T00:00:00Z',
  rest_seconds: 90,
  units: 'kg',
};

function mockApi(
  overrides: {
    sessions?: unknown[];
    prefs?: unknown;
    postSession?: unknown;
  } = {},
) {
  mockApiFetch.mockImplementation((path: string, options?: RequestInit) => {
    if (path === '/auth/me') {
      return Promise.resolve(overrides.prefs ?? PREFS_FIXTURE);
    }
    if (path.startsWith('/workouts/w1/days/day1/sessions')) {
      if (options?.method === 'POST') {
        return Promise.resolve(overrides.postSession ?? SESSION_FIXTURE);
      }
      // GET — returns history (empty by default so we see the pre-start state)
      return Promise.resolve(overrides.sessions ?? []);
    }
    if (path.startsWith('/workouts')) {
      return Promise.resolve(WORKOUT_FIXTURE);
    }
    if (path.startsWith('/exercises')) {
      return Promise.resolve(EXERCISES_FIXTURE);
    }
    return Promise.resolve(undefined);
  });
}

/** Start a session in the UI and wait for exercise cards to appear. */
async function startSession() {
  const user = userEvent.setup();
  mockApi();
  renderWithProviders(<WorkoutSessionPage />);

  // Wait for pre-start state
  const startBtn = await screen.findByRole('button', { name: /Iniciar sesión/ });
  await user.click(startBtn);

  // Wait for exercise blocks to render
  await screen.findByText('Press banca');
  return user;
}

beforeEach(() => {
  useAuthStore.setState({
    token: 'token',
    user: { id: 'u1', email: 'test@example.com', created_at: '2026-01-01T00:00:00Z', rest_seconds: 90, units: 'kg' as const },
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('WorkoutSessionPage', () => {
  it('renders the live timer in mm:ss format after session start', async () => {
    await startSession();

    // The timer element should be visible with mm:ss format
    await waitFor(() => {
      const timerEl = screen.getByLabelText('Tiempo transcurrido');
      expect(timerEl).toBeInTheDocument();
      expect(timerEl.textContent).toMatch(/^\d{2}:\d{2}$/);
    });

    // STARTED_AT is 75 seconds ago, so timer should show at least 01:xx
    const timerEl = screen.getByLabelText('Tiempo transcurrido');
    const [minutes] = (timerEl.textContent ?? '').split(':').map(Number);
    expect(minutes).toBeGreaterThanOrEqual(1);
  });

  it('shows 0/N progress when no sets are done at session start', async () => {
    await startSession();

    // Total sets = 3 (we1) + 2 (we2) = 5
    expect(screen.getByText(/0\/5 series/)).toBeInTheDocument();
    // Progress bar should exist
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuemax', '5');
  });

  it('increments reps stepper by 1 on + click', async () => {
    const user = await startSession();

    // Find the reps stepper group for Serie 1 of the first exercise
    const repsGroups = screen.getAllByRole('group', {
      name: /Repeticiones, serie 1/,
    });
    expect(repsGroups.length).toBeGreaterThan(0);

    const firstGroup = repsGroups[0];
    const incrementBtn = firstGroup.querySelector(
      'button[aria-label="Aumentar"]',
    ) as HTMLElement;
    const valueSpan = firstGroup.querySelector('span.w-10') as HTMLElement;

    const before = parseInt(valueSpan.textContent ?? '0', 10);
    await user.click(incrementBtn);
    const after = parseInt(valueSpan.textContent ?? '0', 10);

    expect(after).toBe(before + 1);
  });

  it('increments weight stepper by 2.5 on + click (default units kg)', async () => {
    const user = await startSession();

    // Find the weight stepper group for Serie 1 of the non-bodyweight exercise
    const weightGroups = screen.getAllByRole('group', {
      name: /Peso kg, serie 1/,
    });
    expect(weightGroups.length).toBeGreaterThan(0);

    const firstWeightGroup = weightGroups[0];
    const incrementBtn = firstWeightGroup.querySelector(
      'button[aria-label="Aumentar"]',
    ) as HTMLElement;
    const valueSpan = firstWeightGroup.querySelector('span.w-10') as HTMLElement;

    const before = parseFloat(valueSpan.textContent ?? '0');
    await user.click(incrementBtn);
    const after = parseFloat(valueSpan.textContent ?? '0');

    expect(after - before).toBeCloseTo(2.5, 1);
  });

  it('hides the weight stepper for bodyweight exercises', async () => {
    await startSession();

    // Weight groups for Dominadas (e2, bodyweight) should NOT exist
    const weightGroupsForBodyweight = screen.queryAllByRole('group', {
      name: /Peso kg, serie.*Dominadas/,
    });
    expect(weightGroupsForBodyweight).toHaveLength(0);

    // "Peso corporal" placeholder text should be visible
    const bodyweightLabels = screen.getAllByText('Peso corporal');
    expect(bodyweightLabels.length).toBeGreaterThan(0);
  });

  it('renders exercises in plan order, not by muscle group', async () => {
    // The fixture has Press banca (Pecho, order=1) before Dominadas (Espalda, order=2).
    // Reversing the order in the day payload verifies the component sorts by `order`,
    // not by insertion order or muscle group.
    const user = userEvent.setup();
    mockApiFetch.mockImplementation((path: string, options?: RequestInit) => {
      if (path === '/auth/me') return Promise.resolve(PREFS_FIXTURE);
      if (path.startsWith('/workouts/w1/days/day1/sessions')) {
        if (options?.method === 'POST') return Promise.resolve(SESSION_FIXTURE);
        return Promise.resolve([]);
      }
      if (path.startsWith('/workouts')) {
        return Promise.resolve({
          ...WORKOUT_FIXTURE,
          training_days: [
            {
              ...WORKOUT_FIXTURE.training_days[0],
              exercises: [
                // Reversed insertion order: Dominadas first in array, but order=2
                { id: 'we2', exercise_id: 'e2', order: 2, sets: 2, reps_per_set: 12, weight_kg: null },
                // Press banca second in array, but order=1
                { id: 'we1', exercise_id: 'e1', order: 1, sets: 3, reps_per_set: 10, weight_kg: 80 },
              ],
            },
          ],
        });
      }
      if (path.startsWith('/exercises')) return Promise.resolve(EXERCISES_FIXTURE);
      return Promise.resolve(undefined);
    });

    renderWithProviders(<WorkoutSessionPage />);
    const startBtn = await screen.findByRole('button', { name: /Iniciar sesión/ });
    await user.click(startBtn);

    await screen.findByText('Press banca');

    const exerciseHeadings = screen.getAllByRole('heading', { level: 3 });
    const names = exerciseHeadings.map((h) => h.textContent ?? '');
    const pressIndex = names.findIndex((n) => n.includes('Press banca'));
    const dominadasIndex = names.findIndex((n) => n.includes('Dominadas'));

    expect(pressIndex).toBeGreaterThanOrEqual(0);
    expect(dominadasIndex).toBeGreaterThanOrEqual(0);
    expect(pressIndex).toBeLessThan(dominadasIndex);
  });
});
