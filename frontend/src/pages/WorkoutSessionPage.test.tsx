import { screen, waitFor, within, act } from '@testing-library/react';
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

// started_at is set fresh in beforeEach so it always reflects the current test run time
let STARTED_AT: string;

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

function makeSessionFixture() {
  return {
    id: 'sess1',
    workout_id: 'w1',
    training_day_id: 'day1',
    started_at: STARTED_AT,
    status: 'in_progress',
    completed_at: null,
    logs: [],
  };
}

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
        return Promise.resolve(overrides.postSession ?? makeSessionFixture());
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
  STARTED_AT = new Date(Date.now() - 75_000).toISOString();
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

  it('updates reps on typing a new value into the input', async () => {
    const user = await startSession();

    // Find the reps input group for Serie 1 of the first exercise
    const repsGroups = screen.getAllByRole('group', {
      name: /Repeticiones, serie 1/,
    });
    expect(repsGroups.length).toBeGreaterThan(0);

    const repsInput = within(repsGroups[0]).getByRole('textbox') as HTMLInputElement;

    await user.clear(repsInput);
    await user.type(repsInput, '12');
    await user.tab(); // blur to commit

    expect(repsInput.value).toBe('12');
  });

  it('updates weight on typing a new value into the input (default units kg)', async () => {
    const user = await startSession();

    // Find the weight input group for Serie 1 of the non-bodyweight exercise
    const weightGroups = screen.getAllByRole('group', {
      name: /Peso kg, serie 1/,
    });
    expect(weightGroups.length).toBeGreaterThan(0);

    const weightInput = within(weightGroups[0]).getByRole('textbox') as HTMLInputElement;

    await user.clear(weightInput);
    await user.type(weightInput, '20');
    await user.tab(); // blur to commit

    expect(weightInput.value).toBe('20');
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
        if (options?.method === 'POST') return Promise.resolve(makeSessionFixture());
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

// ---------------------------------------------------------------------------
// Rest timer
// ---------------------------------------------------------------------------

/** Opens the rest timer panel (assumes session is already active). */
async function openTimer(user: ReturnType<typeof userEvent.setup>) {
  const clockBtn = await screen.findByRole('button', { name: 'Abrir cronómetro' });
  await user.click(clockBtn);
  await screen.findByText('Cronómetro');
}

describe('Rest Timer — panel open/close', () => {
  it('clock button is not visible before session starts', async () => {
    mockApi();
    renderWithProviders(<WorkoutSessionPage />);
    await screen.findByRole('button', { name: /Iniciar sesión/ });
    expect(screen.queryByRole('button', { name: 'Abrir cronómetro' })).not.toBeInTheDocument();
  });

  it('clock button appears after session starts', async () => {
    await startSession();
    expect(screen.getByRole('button', { name: 'Abrir cronómetro' })).toBeInTheDocument();
  });

  it('opens the timer panel on clock button click', async () => {
    const user = await startSession();
    await openTimer(user);
    expect(screen.getByText('Cronómetro')).toBeInTheDocument();
  });

  it('closes the panel with the X button', async () => {
    const user = await startSession();
    await openTimer(user);
    await user.click(screen.getByRole('button', { name: 'Cerrar cronómetro' }));
    expect(screen.queryByText('Cronómetro')).not.toBeInTheDocument();
  });
});

describe('Rest Timer — initial state', () => {
  it('shows 1:30 as default time (90 s preset)', async () => {
    const user = await startSession();
    await openTimer(user);
    expect(screen.getByLabelText('Tiempo del cronómetro')).toHaveTextContent('1:30');
  });

  it('shows "En pausa" status initially', async () => {
    const user = await startSession();
    await openTimer(user);
    expect(screen.getByText('En pausa')).toBeInTheDocument();
  });

  it('shows Iniciar button initially', async () => {
    const user = await startSession();
    await openTimer(user);
    expect(screen.getByRole('button', { name: 'Iniciar' })).toBeInTheDocument();
  });

  it('renders the four preset buttons in rest mode', async () => {
    const user = await startSession();
    await openTimer(user);
    for (const label of ['1:00', '1:30', '2:00', '3:00']) {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument();
    }
  });
});

describe('Rest Timer — controls', () => {
  it('toggles to Pausar and "En marcha" when started', async () => {
    const user = await startSession();
    await openTimer(user);
    await user.click(screen.getByRole('button', { name: 'Iniciar' }));
    expect(screen.getByRole('button', { name: 'Pausar' })).toBeInTheDocument();
    expect(screen.getByText('En marcha')).toBeInTheDocument();
  });

  it('pauses the timer and shows Iniciar again', async () => {
    const user = await startSession();
    await openTimer(user);
    await user.click(screen.getByRole('button', { name: 'Iniciar' }));
    await user.click(screen.getByRole('button', { name: 'Pausar' }));
    expect(screen.getByRole('button', { name: 'Iniciar' })).toBeInTheDocument();
    expect(screen.getByText('En pausa')).toBeInTheDocument();
  });

  it('preset button changes the timer display', async () => {
    const user = await startSession();
    await openTimer(user);
    await user.click(screen.getByRole('button', { name: '2:00' }));
    expect(screen.getByLabelText('Tiempo del cronómetro')).toHaveTextContent('2:00');
  });

  it('reset button restores preset time and stops the timer', async () => {
    const user = await startSession();
    await openTimer(user);
    await user.click(screen.getByRole('button', { name: '2:00' }));
    await user.click(screen.getByRole('button', { name: 'Iniciar' }));
    await user.click(screen.getByRole('button', { name: 'Reiniciar cronómetro' }));
    expect(screen.getByRole('button', { name: 'Iniciar' })).toBeInTheDocument();
    expect(screen.getByLabelText('Tiempo del cronómetro')).toHaveTextContent('2:00');
  });

  it('switching to Ascendente hides preset buttons and shows 0:00', async () => {
    const user = await startSession();
    await openTimer(user);
    await user.click(screen.getByRole('button', { name: 'Ascendente' }));
    expect(screen.queryByRole('button', { name: '1:00' })).not.toBeInTheDocument();
    expect(screen.getByLabelText('Tiempo del cronómetro')).toHaveTextContent('0:00');
  });
});

// NOTE: vi.useFakeTimers fakes setInterval/clearInterval only (not setTimeout, so waitFor still works).
// Advancing fake time fires BOTH the rest timer interval AND the session elapsed-timer interval.
// Tests assert only on rest-timer state — elapsed-timer interference is harmless but present.
// Future changes to session-elapsed timer logic must account for this dual-interval behavior.
describe('Rest Timer — countdown (fake timers)', () => {
  // Only fake setInterval/clearInterval so setTimeout (used by waitFor/findBy) stays real.
  beforeEach(() => { vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] }); });
  afterEach(() => { vi.useRealTimers(); });

  it('counts down after starting', async () => {
    const user = await startSession();
    await openTimer(user);
    await user.click(screen.getByRole('button', { name: 'Iniciar' }));
    act(() => { vi.advanceTimersByTime(5000); });
    await waitFor(() => {
      expect(screen.getByLabelText('Tiempo del cronómetro')).toHaveTextContent('1:25');
    });
  });

  it('shows "¡Descanso completo!" and Reiniciar when countdown ends', async () => {
    const user = await startSession();
    await openTimer(user);
    await user.click(screen.getByRole('button', { name: '1:00' }));
    await user.click(screen.getByRole('button', { name: 'Iniciar' }));
    act(() => { vi.advanceTimersByTime(60_000); });
    await waitFor(() => {
      expect(screen.getByText('¡Descanso completo!')).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: 'Reiniciar' })).toBeInTheDocument();
  });

  it('"Reiniciar" after completion resets and starts again', async () => {
    const user = await startSession();
    await openTimer(user);
    await user.click(screen.getByRole('button', { name: '1:00' }));
    await user.click(screen.getByRole('button', { name: 'Iniciar' }));
    act(() => { vi.advanceTimersByTime(60_000); });
    await waitFor(() => screen.getByText('¡Descanso completo!'));
    await user.click(screen.getByRole('button', { name: 'Reiniciar' }));
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Pausar' })).toBeInTheDocument();
    });
    expect(screen.getByLabelText('Tiempo del cronómetro')).toHaveTextContent('1:00');
  });

  it('ascending mode counts up', async () => {
    const user = await startSession();
    await openTimer(user);
    await user.click(screen.getByRole('button', { name: 'Ascendente' }));
    await user.click(screen.getByRole('button', { name: 'Iniciar' }));
    act(() => { vi.advanceTimersByTime(5000); });
    await waitFor(() => {
      expect(screen.getByLabelText('Tiempo del cronómetro')).toHaveTextContent('0:05');
    });
  });
});
