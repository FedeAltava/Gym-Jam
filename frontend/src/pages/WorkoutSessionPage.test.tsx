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
  { id: 'e3', name: 'Aperturas con mancuernas', muscle_group: 'Pecho', is_bodyweight: false },
  { id: 'e4', name: 'Remo con barra', muscle_group: 'Espalda', is_bodyweight: false },
  { id: 'chest-press-plate-loaded', name: 'Press pecho en máquina (discos)', muscle_group: 'Pecho', is_bodyweight: false },
  { id: 'chest-press-selectorized', name: 'Press pecho en máquina (placas)', muscle_group: 'Pecho', is_bodyweight: false },
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
    lastSets?: unknown[];
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
    if (path.startsWith('/exercises/last-sets')) {
      return Promise.resolve(overrides.lastSets ?? []);
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

/** Simulate the phone locking (page hidden) or unlocking (page visible). */
function setPageHidden(hidden: boolean) {
  Object.defineProperty(document, 'hidden', { configurable: true, get: () => hidden });
  Object.defineProperty(document, 'visibilityState', {
    configurable: true,
    get: () => (hidden ? 'hidden' : 'visible'),
  });
  act(() => { document.dispatchEvent(new Event('visibilitychange')); });
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

    // Verify the element exists and shows the expected mm:ss format.
    await waitFor(() => {
      const timerEl = screen.getByLabelText('Tiempo transcurrido');
      expect(timerEl).toBeInTheDocument();
      expect(timerEl.textContent).toMatch(/^\d{2}:\d{2}$/);
    });
  });

  it('counts the session time from the server start time', async () => {
    vi.useFakeTimers({ toFake: ['Date', 'setInterval', 'clearInterval'] });
    try {
      await startSession();

      await waitFor(() => {
        expect(screen.getByLabelText('Tiempo transcurrido')).toHaveTextContent('01:15');
      });
    } finally {
      vi.useRealTimers();
    }
  });

  it('keeps counting the session time while the screen is locked', async () => {
    vi.useFakeTimers({ toFake: ['Date', 'setInterval', 'clearInterval'] });
    try {
      await startSession();
      await waitFor(() => {
        expect(screen.getByLabelText('Tiempo transcurrido')).toHaveTextContent('01:15');
      });

      setPageHidden(true);
      // The browser freezes intervals while locked: only the clock moves.
      vi.setSystemTime(Date.now() + 10 * 60_000);
      setPageHidden(false);

      expect(screen.getByLabelText('Tiempo transcurrido')).toHaveTextContent('11:15');
    } finally {
      setPageHidden(false);
      vi.useRealTimers();
    }
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

  it.each(['12,5', '12.5'])('accepts a decimal weight typed as %s and logs it', async (typed) => {
    const user = await startSession();
    const weightInput = within(screen.getAllByRole('group', { name: /Peso kg, serie 1/ })[0]).getByRole(
      'textbox',
    ) as HTMLInputElement;

    await user.clear(weightInput);
    await user.type(weightInput, typed);
    await user.tab(); // blur to commit

    expect(weightInput.value).toBe('12,5');
    await user.click(screen.getAllByRole('button', { name: 'Marcar serie 1 como hecha' })[0]);
    const post = mockApiFetch.mock.calls.find(([path, options]) => path === '/sessions/sess1/logs' && options?.method === 'POST');
    expect(JSON.parse(post?.[1]?.body as string).weight_kg).toBe(12.5);
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

/** Opens the rest timer panel (assumes session is already active).
 *  The page renders two "Abrir cronómetro" buttons (header + floating FAB),
 *  so we click the first one found. */
async function openTimer(user: ReturnType<typeof userEvent.setup>) {
  const clockBtns = await screen.findAllByRole('button', { name: 'Abrir cronómetro' });
  await user.click(clockBtns[0]);
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
    // Both the header button and the floating FAB render with this label.
    const btns = screen.getAllByRole('button', { name: 'Abrir cronómetro' });
    expect(btns.length).toBeGreaterThanOrEqual(1);
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
  // Fake the clock and setInterval only, so setTimeout (used by waitFor/findBy) stays real.
  beforeEach(() => { vi.useFakeTimers({ toFake: ['Date', 'setInterval', 'clearInterval'] }); });
  afterEach(() => {
    setPageHidden(false);
    vi.useRealTimers();
  });

  it('keeps counting down while the screen is locked', async () => {
    const user = await startSession();
    await openTimer(user);
    await user.click(screen.getByRole('button', { name: 'Iniciar' }));

    setPageHidden(true);
    // The browser freezes intervals while locked: only the clock moves.
    vi.setSystemTime(Date.now() + 30_000);
    setPageHidden(false);

    expect(screen.getByLabelText('Tiempo del cronómetro')).toHaveTextContent('1:00');
  });

  it('ascending mode keeps counting while the screen is locked', async () => {
    const user = await startSession();
    await openTimer(user);
    await user.click(screen.getByRole('button', { name: 'Ascendente' }));
    await user.click(screen.getByRole('button', { name: 'Iniciar' }));

    setPageHidden(true);
    vi.setSystemTime(Date.now() + 30_000);
    setPageHidden(false);

    expect(screen.getByLabelText('Tiempo del cronómetro')).toHaveTextContent('0:30');
  });

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

// ---------------------------------------------------------------------------
// Exercise swap — replace a planned exercise for this session only
// ---------------------------------------------------------------------------

type SwapFixture = { workout_exercise_id: string; exercise_id: string };

/** Resume an in-progress session whose swaps live on a fake server. */
async function resumeSession(
  initial: {
    swaps?: SwapFixture[];
    logs?: unknown[];
    history?: unknown[];
    lastSets?: unknown[] | Promise<unknown[]> | (() => Promise<unknown[]>);
    workout?: typeof WORKOUT_FIXTURE;
    exercises?: typeof EXERCISES_FIXTURE;
    swapError?: Error;
  } = {},
) {
  const live = { ...makeSessionFixture(), logs: initial.logs ?? [], swaps: initial.swaps ?? [] };
  sessionStorage.setItem('gymjam:active-session:w1:day1', 'sess1');
  mockApiFetch.mockImplementation((path: string, options?: RequestInit) => {
    if (path === '/auth/me') return Promise.resolve(PREFS_FIXTURE);
    const swap = path.match(/^\/sessions\/sess1\/exercises\/(\w+)\/swap$/);
    if (swap && options?.method === 'PUT') {
      if (initial.swapError) return Promise.reject(initial.swapError);
      const { exercise_id } = JSON.parse(options.body as string);
      live.swaps = [
        ...live.swaps.filter((s) => s.workout_exercise_id !== swap[1]),
        { workout_exercise_id: swap[1], exercise_id },
      ];
      return Promise.resolve(live);
    }
    if (swap && options?.method === 'DELETE') {
      live.swaps = live.swaps.filter((s) => s.workout_exercise_id !== swap[1]);
      return Promise.resolve(live);
    }
    if (path.startsWith('/workouts/w1/days/day1/sessions')) return Promise.resolve([live, ...(initial.history ?? [])]);
    if (path.startsWith('/workouts')) return Promise.resolve(initial.workout ?? WORKOUT_FIXTURE);
    if (path.startsWith('/exercises/last-sets')) {
      return typeof initial.lastSets === 'function' ? initial.lastSets() : Promise.resolve(initial.lastSets ?? []);
    }
    if (path.startsWith('/exercises')) return Promise.resolve(initial.exercises ?? EXERCISES_FIXTURE);
    return Promise.resolve(undefined);
  });
  const user = userEvent.setup();
  renderWithProviders(<WorkoutSessionPage />);
  await screen.findByText('Dominadas');
  return user;
}

describe('Exercise swap', () => {
  afterEach(() => sessionStorage.clear());

  it('swaps a planned exercise for another catalog exercise', async () => {
    const user = await resumeSession();

    await user.click(screen.getByRole('button', { name: 'Cambiar ejercicio Press banca' }));
    const dialog = screen.getByRole('dialog', { name: 'Cambiar Press banca' });
    // Defaults to the same muscle group and hides the current exercise.
    expect(within(dialog).getByText('Aperturas con mancuernas')).toBeInTheDocument();
    expect(within(dialog).queryByText('Remo con barra')).not.toBeInTheDocument();
    expect(within(dialog).queryByText('Press banca')).not.toBeInTheDocument();
    await user.click(within(dialog).getByRole('button', { name: 'Todos' }));
    expect(within(dialog).getByText('Remo con barra')).toBeInTheDocument();

    await user.click(within(dialog).getByText('Aperturas con mancuernas'));

    expect(mockApiFetch).toHaveBeenCalledWith('/sessions/sess1/exercises/we1/swap', {
      method: 'PUT',
      body: JSON.stringify({ exercise_id: 'e3' }),
    });
    expect(await screen.findByRole('heading', { name: 'Aperturas con mancuernas' })).toBeInTheDocument();
    expect(screen.getByText('En lugar de Press banca')).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('shows the substitute without the planned weight and can undo the swap', async () => {
    const user = await resumeSession({ swaps: [{ workout_exercise_id: 'we1', exercise_id: 'e3' }] });

    expect(await screen.findByRole('heading', { name: 'Aperturas con mancuernas' })).toBeInTheDocument();
    expect(screen.getByText('En lugar de Press banca')).toBeInTheDocument();
    // The plan's 80 kg belongs to Press banca, not to the substitute.
    const weightGroup = screen.getAllByRole('group', { name: /Peso kg, serie 1/ })[0];
    expect((within(weightGroup).getByRole('textbox') as HTMLInputElement).value).toBe('0');

    await user.click(screen.getByRole('button', { name: 'Deshacer cambio de Aperturas con mancuernas' }));

    expect(mockApiFetch).toHaveBeenCalledWith('/sessions/sess1/exercises/we1/swap', { method: 'DELETE' });
    expect(await screen.findByRole('heading', { name: 'Press banca' })).toBeInTheDocument();
    expect(screen.queryByText('En lugar de Press banca')).not.toBeInTheDocument();
  });

  it('clears a failed swap error when the sheet is closed', async () => {
    const user = await resumeSession({ swapError: new Error('boom') });
    await user.click(screen.getByRole('button', { name: 'Cambiar ejercicio Press banca' }));
    const dialog = screen.getByRole('dialog', { name: 'Cambiar Press banca' });
    await user.click(within(dialog).getByText('Aperturas con mancuernas'));
    await within(dialog).findByText('No se pudo cambiar el ejercicio. Inténtalo de nuevo.');

    await user.click(within(dialog).getByRole('button', { name: 'Cerrar' }));

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(screen.queryByText('No se pudo cambiar el ejercicio. Inténtalo de nuevo.')).not.toBeInTheDocument();
  });

  it('does not offer a swap once a set of that exercise is logged', async () => {
    await resumeSession({
      logs: [
        { id: 'l1', session_id: 'sess1', workout_exercise_id: 'we1', set_number: 1, reps_completed: 10, weight_kg: 80 },
      ],
    });

    expect(screen.queryByRole('button', { name: 'Cambiar ejercicio Press banca' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cambiar ejercicio Dominadas' })).toBeInTheDocument();
  });
});

describe('Main exercise', () => {
  afterEach(() => sessionStorage.clear());

  it('highlights the first exercise of the day as the main one', async () => {
    await resumeSession();

    expect(within(screen.getByRole('region', { name: 'Ejercicio Press banca' })).getByText('Principal')).toBeInTheDocument();
    expect(within(screen.getByRole('region', { name: 'Ejercicio Dominadas' })).queryByText('Principal')).not.toBeInTheDocument();
  });
});

describe('Session completed by the server', () => {
  afterEach(() => sessionStorage.clear());

  it('offers a new session once the server completes the open one for inactivity', async () => {
    const live = { ...makeSessionFixture(), logs: [], swaps: [] as SwapFixture[], completed_at: null as string | null };
    sessionStorage.setItem('gymjam:active-session:w1:day1', 'sess1');
    mockApiFetch.mockImplementation((path: string) => {
      if (path === '/auth/me') return Promise.resolve(PREFS_FIXTURE);
      if (path.startsWith('/workouts/w1/days/day1/sessions')) return Promise.resolve([{ ...live }]);
      if (path.startsWith('/workouts')) return Promise.resolve(WORKOUT_FIXTURE);
      if (path.startsWith('/exercises/last-sets')) return Promise.resolve([]);
      if (path.startsWith('/exercises')) return Promise.resolve(EXERCISES_FIXTURE);
      return Promise.resolve(undefined);
    });
    const { queryClient } = renderWithProviders(<WorkoutSessionPage />);
    await screen.findByText('Dominadas');

    live.status = 'completed';
    live.completed_at = STARTED_AT;
    await act(() => queryClient.invalidateQueries({ queryKey: ['sessions'] }));

    expect(await screen.findByRole('button', { name: /Iniciar sesión/ })).toBeInTheDocument();
    expect(screen.queryByLabelText('Tiempo transcurrido')).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Set suggestions — the latest logged sets of the exercise actually done
// ---------------------------------------------------------------------------

function lastSet(exercise_id: string, set_number: number, reps_completed: number, weight_kg: number | null) {
  return { exercise_id, set_number, reps_completed, weight_kg };
}

function suggestedSet(setNumber: number) {
  const reps = screen.getAllByRole('group', { name: `Repeticiones, serie ${setNumber}` })[0];
  const weight = screen.getAllByRole('group', { name: `Peso kg, serie ${setNumber}` })[0];
  return {
    reps: (within(reps).getByRole('textbox') as HTMLInputElement).value,
    weight: (within(weight).getByRole('textbox') as HTMLInputElement).value,
  };
}

describe('Set suggestions from the last time the exercise was done', () => {
  afterEach(() => sessionStorage.clear());

  it('asks for the last sets of the exercises done this session', async () => {
    await resumeSession();

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith('/exercises/last-sets?exercise_id=e1&exercise_id=e2');
    });
  });

  it('suggests each set from the last sets of its exercise', async () => {
    await resumeSession({ lastSets: [lastSet('e1', 1, 9, 90), lastSet('e1', 2, 8, 92.5)] });

    await waitFor(() => expect(suggestedSet(1)).toEqual({ reps: '9', weight: '90' }));
    expect(suggestedSet(2)).toEqual({ reps: '8', weight: '92,5' });
    // No logged set 3 for this exercise yet: plan values.
    expect(suggestedSet(3)).toEqual({ reps: '10', weight: '80' });
  });

  it('suggests a swapped exercise from its own last sets', async () => {
    await resumeSession({
      swaps: [{ workout_exercise_id: 'we1', exercise_id: 'e3' }],
      lastSets: [lastSet('e1', 1, 9, 90), lastSet('e3', 1, 12, 20)],
    });

    await waitFor(() => expect(suggestedSet(1)).toEqual({ reps: '12', weight: '20' }));
  });

  it('falls back to the plan values when the exercise was never logged', async () => {
    await resumeSession({ lastSets: [] });

    await waitFor(() => expect(mockApiFetch).toHaveBeenCalledWith(expect.stringContaining('/exercises/last-sets')));
    expect(suggestedSet(1)).toEqual({ reps: '10', weight: '80' });
  });

  it('keeps plan values and logging working when the last sets cannot be loaded', async () => {
    const failedLoad = Promise.reject(new Error('down'));
    failedLoad.catch(() => {});
    const user = await resumeSession({ lastSets: () => failedLoad });
    await act(async () => { await failedLoad.catch(() => {}); });

    expect(mockApiFetch).toHaveBeenCalledWith('/exercises/last-sets?exercise_id=e1&exercise_id=e2');
    expect(suggestedSet(1)).toEqual({ reps: '10', weight: '80' });
    await user.click(screen.getAllByRole('button', { name: 'Marcar serie 1 como hecha' })[0]);
    expect(mockApiFetch).toHaveBeenCalledWith('/sessions/sess1/logs', expect.objectContaining({ method: 'POST' }));
  });

  it('never overwrites a logged set with late suggestions', async () => {
    let resolveLastSets: (sets: unknown[]) => void = () => {};
    const lastSets = new Promise<unknown[]>((resolve) => { resolveLastSets = resolve; });
    await resumeSession({
      lastSets,
      logs: [{ id: 'l1', session_id: 'sess1', workout_exercise_id: 'we1', set_number: 1, reps_completed: 10, weight_kg: 40 }],
    });

    await act(async () => { resolveLastSets([lastSet('e1', 1, 9, 90), lastSet('e1', 2, 8, 95)]); });

    await waitFor(() => expect(suggestedSet(2)).toEqual({ reps: '8', weight: '95' }));
    expect(suggestedSet(1)).toEqual({ reps: '10', weight: '40' });
  });

  it('applies suggestions that arrive after the sets are shown, unless the set was edited', async () => {
    let resolveLastSets: (sets: unknown[]) => void = () => {};
    const lastSets = new Promise<unknown[]>((resolve) => { resolveLastSets = resolve; });
    const user = await resumeSession({ lastSets });
    expect(suggestedSet(1)).toEqual({ reps: '10', weight: '80' });
    const set2Weight = within(screen.getAllByRole('group', { name: 'Peso kg, serie 2' })[0]).getByRole('textbox');
    await user.clear(set2Weight);
    await user.type(set2Weight, '70{Enter}');

    await act(async () => { resolveLastSets([lastSet('e1', 1, 9, 90), lastSet('e1', 2, 8, 95)]); });

    await waitFor(() => expect(suggestedSet(1)).toEqual({ reps: '9', weight: '90' }));
    expect(suggestedSet(2).weight).toBe('70');
  });
});

// ---------------------------------------------------------------------------
// Machine twin — one tap to the other machine type of the same exercise
// ---------------------------------------------------------------------------

const VARIANT_WORKOUT = {
  ...WORKOUT_FIXTURE,
  training_days: [
    {
      ...WORKOUT_FIXTURE.training_days[0],
      exercises: [
        { ...WORKOUT_FIXTURE.training_days[0].exercises[0], exercise_id: 'chest-press-plate-loaded' },
        WORKOUT_FIXTURE.training_days[0].exercises[1],
      ],
    },
  ],
};

describe('Switch to the other machine type', () => {
  afterEach(() => sessionStorage.clear());

  it('switches a plate-loaded machine to its selectorized twin in one tap', async () => {
    const user = await resumeSession({ workout: VARIANT_WORKOUT });

    await user.click(await screen.findByRole('button', { name: 'Cambiar a placas' }));

    expect(mockApiFetch).toHaveBeenCalledWith('/sessions/sess1/exercises/we1/swap', {
      method: 'PUT',
      body: JSON.stringify({ exercise_id: 'chest-press-selectorized' }),
    });
    expect(await screen.findByRole('heading', { name: 'Press pecho en máquina (placas)' })).toBeInTheDocument();
    // Back to the planned machine in one tap too; the generic switch stays.
    expect(screen.getByRole('button', { name: 'Cambiar a discos' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cambiar ejercicio Press pecho en máquina (placas)' })).toBeInTheDocument();
  });

  it('switches back to the planned machine in one tap', async () => {
    const user = await resumeSession({
      workout: VARIANT_WORKOUT,
      swaps: [{ workout_exercise_id: 'we1', exercise_id: 'chest-press-selectorized' }],
    });

    await user.click(await screen.findByRole('button', { name: 'Cambiar a discos' }));

    expect(mockApiFetch).toHaveBeenCalledWith('/sessions/sess1/exercises/we1/swap', {
      method: 'PUT',
      body: JSON.stringify({ exercise_id: 'chest-press-plate-loaded' }),
    });
  });

  it('shows a failed machine switch on that exercise', async () => {
    const user = await resumeSession({ workout: VARIANT_WORKOUT, swapError: new Error('boom') });

    await user.click(await screen.findByRole('button', { name: 'Cambiar a placas' }));

    expect(await screen.findByText('No se pudo cambiar el ejercicio. Inténtalo de nuevo.')).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Press pecho en máquina (discos)' })).toBeInTheDocument();
  });

  it('offers no machine switch when the twin is not in the catalog', async () => {
    const workout = {
      ...VARIANT_WORKOUT,
      training_days: [
        {
          ...VARIANT_WORKOUT.training_days[0],
          exercises: [
            { ...VARIANT_WORKOUT.training_days[0].exercises[0], exercise_id: 'lat-pulldown-plate-loaded' },
            VARIANT_WORKOUT.training_days[0].exercises[1],
          ],
        },
      ],
    };
    const exercises = [
      ...EXERCISES_FIXTURE,
      { id: 'lat-pulldown-plate-loaded', name: 'Jalón (discos)', muscle_group: 'Espalda', is_bodyweight: false },
    ];
    await resumeSession({ workout, exercises });

    await screen.findByRole('heading', { name: 'Jalón (discos)' });
    expect(screen.queryByRole('button', { name: /Cambiar a (placas|discos)/ })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cambiar ejercicio Jalón (discos)' })).toBeInTheDocument();
  });

  it('offers no machine switch for exercises without a twin or with logged sets', async () => {
    await resumeSession({
      workout: VARIANT_WORKOUT,
      logs: [
        { id: 'l1', session_id: 'sess1', workout_exercise_id: 'we1', set_number: 1, reps_completed: 10, weight_kg: 40 },
      ],
    });

    await screen.findByRole('heading', { name: 'Press pecho en máquina (discos)' });
    expect(screen.queryByRole('button', { name: /Cambiar a (placas|discos)/ })).not.toBeInTheDocument();
  });
});
