import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/test-utils';
import { AddExercisesPage } from './AddExercisesPage';
import { useAuthStore } from '../store/authStore';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

// The page uses `useParams` with { workoutId, day } — note `day`, NOT `dayId`
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return {
    ...actual,
    useParams: vi.fn(() => ({ workoutId: 'w1', day: 'MONDAY' })),
    useNavigate: vi.fn(() => vi.fn()),
  };
});

import { apiFetch } from '../lib/api';
import { useNavigate } from 'react-router-dom';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;
const mockUseNavigate = useNavigate as ReturnType<typeof vi.fn>;

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const EXERCISES_FIXTURE = [
  { id: 'e1', name: 'Press banca', muscle_group: 'Pecho', is_bodyweight: false },
  { id: 'e2', name: 'Press militar', muscle_group: 'Hombros', is_bodyweight: false },
  { id: 'e3', name: 'Dominadas', muscle_group: 'Espalda', is_bodyweight: true },
  { id: 'e4', name: 'Sentadilla', muscle_group: 'Piernas', is_bodyweight: false },
];

const WORKOUT_FIXTURE = {
  id: 'w1',
  name: 'Push Pull Legs',
  description: null,
  is_active: true,
  training_days: [
    {
      id: 'day1',
      day_of_week: 'MONDAY',
      order: 0,
      exercises: [
        // e1 is already in the Monday day
        { id: 'we1', exercise_id: 'e1', order: 1, sets: 3, reps_per_set: 10, weight_kg: 80 },
      ],
    },
  ],
};

const WORKOUT_EMPTY_DAY_FIXTURE = {
  ...WORKOUT_FIXTURE,
  training_days: [
    {
      id: 'day1',
      day_of_week: 'MONDAY',
      order: 0,
      exercises: [],
    },
  ],
};

function mockApi(overrides: { workout?: unknown; exercises?: unknown } = {}) {
  mockApiFetch.mockImplementation((path: string, options?: RequestInit) => {
    if (path === '/exercises') {
      return Promise.resolve(overrides.exercises ?? EXERCISES_FIXTURE);
    }
    if (path.startsWith('/workouts/w1') && !options?.method) {
      return Promise.resolve(overrides.workout ?? WORKOUT_FIXTURE);
    }
    if (path.includes('/training-days/') && options?.method === 'POST') {
      return Promise.resolve({ id: 'we-new', exercise_id: 'e2', order: 2, sets: 3, reps_per_set: 10, weight_kg: null });
    }
    return Promise.resolve(undefined);
  });
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

describe('AddExercisesPage', () => {
  it('renders exercises from the catalog', async () => {
    mockApi();
    renderWithProviders(<AddExercisesPage />);

    // e1 (Press banca) is already in the workout — should NOT appear
    // The other 3 should appear
    expect(await screen.findByText('Press militar')).toBeInTheDocument();
    expect(screen.getByText('Dominadas')).toBeInTheDocument();
    expect(screen.getByText('Sentadilla')).toBeInTheDocument();
  });

  it('shows muscle group labels alongside exercise names', async () => {
    mockApi();
    renderWithProviders(<AddExercisesPage />);

    await screen.findByText('Press militar');
    // Each exercise <li> contains a <p> with the muscle group name.
    // getAllByText is used because the muscle group text also appears in the filter buttons.
    expect(screen.getAllByText('Hombros').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Espalda').length).toBeGreaterThanOrEqual(1);
  });

  it('renders muscle group filter buttons', async () => {
    mockApi();
    renderWithProviders(<AddExercisesPage />);

    await screen.findByText('Press militar');

    // "Todos" is always present; individual groups for the displayed exercises
    expect(screen.getByRole('button', { name: 'Todos' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hombros' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Espalda' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Piernas' })).toBeInTheDocument();
  });

  it('filters exercises by muscle group when a group button is clicked', async () => {
    const user = userEvent.setup();
    mockApi();
    renderWithProviders(<AddExercisesPage />);

    await screen.findByText('Press militar');

    // Initially all 3 available exercises are shown
    expect(screen.getByText('Press militar')).toBeInTheDocument();
    expect(screen.getByText('Dominadas')).toBeInTheDocument();

    // Click the Hombros filter
    await user.click(screen.getByRole('button', { name: 'Hombros' }));

    // Only Hombros exercises remain
    expect(screen.getByText('Press militar')).toBeInTheDocument();
    expect(screen.queryByText('Dominadas')).not.toBeInTheDocument();
    expect(screen.queryByText('Sentadilla')).not.toBeInTheDocument();
  });

  it('clicking Todos after a filter shows all exercises again', async () => {
    const user = userEvent.setup();
    mockApi();
    renderWithProviders(<AddExercisesPage />);

    await screen.findByText('Press militar');

    await user.click(screen.getByRole('button', { name: 'Hombros' }));
    expect(screen.queryByText('Dominadas')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Todos' }));
    expect(screen.getByText('Dominadas')).toBeInTheDocument();
  });

  it('selects an exercise when clicked and shows the checkmark', async () => {
    const user = userEvent.setup();
    mockApi();
    renderWithProviders(<AddExercisesPage />);

    await screen.findByText('Press militar');

    const pressMilitarItem = screen.getByText('Press militar').closest('li')!;
    expect(pressMilitarItem).toHaveAttribute('aria-checked', 'false');

    await user.click(pressMilitarItem);

    expect(pressMilitarItem).toHaveAttribute('aria-checked', 'true');
  });

  it('deselects an exercise when clicked again', async () => {
    const user = userEvent.setup();
    mockApi();
    renderWithProviders(<AddExercisesPage />);

    await screen.findByText('Press militar');

    const pressMilitarItem = screen.getByText('Press militar').closest('li')!;
    await user.click(pressMilitarItem);
    expect(pressMilitarItem).toHaveAttribute('aria-checked', 'true');

    await user.click(pressMilitarItem);
    expect(pressMilitarItem).toHaveAttribute('aria-checked', 'false');
  });

  it('add button is disabled when no exercises are selected', async () => {
    mockApi();
    renderWithProviders(<AddExercisesPage />);

    await screen.findByText('Press militar');

    const addBtn = screen.getByRole('button', { name: /Añadir 0/ });
    expect(addBtn).toBeDisabled();
  });

  it('add button shows count of selected exercises', async () => {
    const user = userEvent.setup();
    mockApi();
    renderWithProviders(<AddExercisesPage />);

    await screen.findByText('Press militar');

    await user.click(screen.getByText('Press militar').closest('li')!);
    expect(screen.getByRole('button', { name: 'Añadir 1 ejercicio' })).toBeInTheDocument();

    await user.click(screen.getByText('Dominadas').closest('li')!);
    expect(screen.getByRole('button', { name: 'Añadir 2 ejercicios' })).toBeInTheDocument();
  });

  it('calls apiFetch for each selected exercise and navigates on success', async () => {
    const user = userEvent.setup();
    const mockNavigate = vi.fn();
    mockUseNavigate.mockReturnValue(mockNavigate);
    mockApi();
    renderWithProviders(<AddExercisesPage />);

    await screen.findByText('Press militar');

    // Select Press militar (e2) and Dominadas (e3)
    await user.click(screen.getByText('Press militar').closest('li')!);
    await user.click(screen.getByText('Dominadas').closest('li')!);

    await user.click(screen.getByRole('button', { name: 'Añadir 2 ejercicios' }));

    // useBatchAddExercises posts one apiFetch per exercise
    await waitFor(() => {
      const postCalls = mockApiFetch.mock.calls.filter(
        ([, opts]: [string, RequestInit]) => opts?.method === 'POST',
      );
      expect(postCalls).toHaveLength(2);
    });

    // Both exercise IDs should appear in the POST payloads
    const postPayloads = mockApiFetch.mock.calls
      .filter(([, opts]: [string, RequestInit]) => opts?.method === 'POST')
      .map(([, opts]: [string, RequestInit]) => JSON.parse(opts.body as string));

    expect(postPayloads).toEqual(
      expect.arrayContaining([
        { exercise_id: 'e2' },
        { exercise_id: 'e3' },
      ]),
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/workouts/w1');
    });
  });

  it('disables the button while the mutation is in-flight (prevents double submit)', async () => {
    const user = userEvent.setup();
    mockUseNavigate.mockReturnValue(vi.fn());

    // Make the POST hang so we can inspect the in-flight state
    let resolvePost!: () => void;
    mockApiFetch.mockImplementation((path: string, options?: RequestInit) => {
      if (path === '/exercises') return Promise.resolve(EXERCISES_FIXTURE);
      if (path.startsWith('/workouts/w1') && !options?.method) return Promise.resolve(WORKOUT_FIXTURE);
      if (options?.method === 'POST') {
        return new Promise<void>((resolve) => { resolvePost = resolve; });
      }
      return Promise.resolve(undefined);
    });

    renderWithProviders(<AddExercisesPage />);
    await screen.findByText('Press militar');

    await user.click(screen.getByText('Press militar').closest('li')!);
    const addBtn = screen.getByRole('button', { name: 'Añadir 1 ejercicio' });
    await user.click(addBtn);

    // Button should be disabled and show "Añadiendo…"
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Añadiendo…' })).toBeDisabled();
    });

    // Clicking again must not send a second request
    await user.click(screen.getByRole('button', { name: 'Añadiendo…' }));

    // Only 1 POST should have been fired (the first click)
    const postCalls = mockApiFetch.mock.calls.filter(
      ([, opts]: [string, RequestInit]) => opts?.method === 'POST',
    );
    expect(postCalls).toHaveLength(1);

    // Clean up the hanging promise
    resolvePost();
  });

  it('shows an error message when the POST fails and re-enables the button', async () => {
    const user = userEvent.setup();
    mockUseNavigate.mockReturnValue(vi.fn());

    mockApiFetch.mockImplementation((path: string, options?: RequestInit) => {
      if (path === '/exercises') return Promise.resolve(EXERCISES_FIXTURE);
      if (path.startsWith('/workouts/w1') && !options?.method) return Promise.resolve(WORKOUT_FIXTURE);
      if (options?.method === 'POST') return Promise.reject(new Error('Server error'));
      return Promise.resolve(undefined);
    });

    renderWithProviders(<AddExercisesPage />);
    await screen.findByText('Press militar');

    await user.click(screen.getByText('Press militar').closest('li')!);
    await user.click(screen.getByRole('button', { name: 'Añadir 1 ejercicio' }));

    await screen.findByText('No se pudieron añadir los ejercicios. Inténtalo de nuevo.');

    // Button should be re-enabled after failure
    const addBtn = screen.getByRole('button', { name: 'Añadir 1 ejercicio' });
    expect(addBtn).not.toBeDisabled();
  });

  it('hides already-added exercises (they do not appear in the list)', async () => {
    mockApi();
    renderWithProviders(<AddExercisesPage />);

    // Wait for the page to load
    await screen.findByText('Press militar');

    // Press banca (e1) is in the workout for MONDAY — must not appear in the catalog list
    expect(screen.queryByText('Press banca')).not.toBeInTheDocument();
  });

  it('shows "No hay ejercicios disponibles" when all catalog exercises are already added', async () => {
    // All exercises in the catalog are already in the day
    const fullWorkout = {
      ...WORKOUT_FIXTURE,
      training_days: [
        {
          id: 'day1',
          day_of_week: 'MONDAY',
          order: 0,
          exercises: EXERCISES_FIXTURE.map((e, i) => ({
            id: `we${i}`,
            exercise_id: e.id,
            order: i + 1,
            sets: 3,
            reps_per_set: 10,
            weight_kg: null,
          })),
        },
      ],
    };

    mockApi({ workout: fullWorkout });
    renderWithProviders(<AddExercisesPage />);

    expect(await screen.findByText('No hay ejercicios disponibles.')).toBeInTheDocument();
  });

  it('shows a loading spinner while the catalog is being fetched', () => {
    // Never resolve the exercises fetch so we stay in loading state
    mockApiFetch.mockImplementation((path: string) => {
      if (path.startsWith('/workouts')) return Promise.resolve(WORKOUT_EMPTY_DAY_FIXTURE);
      return new Promise(() => {}); // hangs forever
    });

    renderWithProviders(<AddExercisesPage />);

    // The spinner element should be in the DOM
    expect(document.querySelector('[class*="spinner"], svg.animate-spin, [data-testid="spinner"]') ||
      document.querySelector('.animate-spin')).toBeTruthy();
  });

  it('shows an error message when the catalog fetch fails', async () => {
    mockApiFetch.mockImplementation((path: string) => {
      if (path.startsWith('/workouts')) return Promise.resolve(WORKOUT_EMPTY_DAY_FIXTURE);
      return Promise.reject(new Error('Network error'));
    });

    renderWithProviders(<AddExercisesPage />);

    expect(
      await screen.findByText('No se pudo cargar el catálogo de ejercicios. Inténtalo de nuevo.'),
    ).toBeInTheDocument();
  });
});
