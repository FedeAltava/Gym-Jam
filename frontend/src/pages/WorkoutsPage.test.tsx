import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/test-utils';
import { WorkoutsPage } from './WorkoutsPage';
import { DAYS } from '../lib/days';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../lib/api';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

const TODAY_KEY = DAYS[(new Date().getDay() + 6) % 7];

const ACTIVE_WORKOUT = {
  id: 'w1',
  name: 'Push Pull Legs',
  description: 'Rutina de fuerza',
  is_active: true,
  training_days: [
    {
      id: 'day-today',
      day_of_week: TODAY_KEY,
      order: 0,
      exercises: [
        { id: 'we1', exercise_id: 'e1', order: 1, sets: 3, reps_per_set: 10, weight_kg: 80 },
        { id: 'we2', exercise_id: 'e2', order: 2, sets: 3, reps_per_set: 12, weight_kg: null },
      ],
    },
  ],
};

const INACTIVE_WORKOUT = {
  ...ACTIVE_WORKOUT,
  id: 'w2',
  name: 'Rutina Vieja',
  is_active: false,
};

function mockWorkouts(workouts: unknown[]) {
  mockApiFetch.mockImplementation((path: string) => {
    if (path.startsWith('/workouts')) return Promise.resolve(workouts);
    return Promise.resolve(undefined);
  });
}

afterEach(() => {
  vi.clearAllMocks();
});

describe('WorkoutsPage', () => {
  it('renders workout cards with name, Activo badge and exercise count', async () => {
    mockWorkouts([ACTIVE_WORKOUT, INACTIVE_WORKOUT]);
    renderWithProviders(<WorkoutsPage />);

    expect(await screen.findByText('Push Pull Legs')).toBeInTheDocument();
    expect(screen.getByText('Rutina Vieja')).toBeInTheDocument();
    expect(screen.getByText('Activo')).toBeInTheDocument();
    expect(screen.getAllByText(/2 ejercicios/)).toHaveLength(2);
  });

  it('shows the Empezar hoy button only on the active workout when today is a plan day', async () => {
    mockWorkouts([ACTIVE_WORKOUT, INACTIVE_WORKOUT]);
    renderWithProviders(<WorkoutsPage />);

    expect(await screen.findByText('Push Pull Legs')).toBeInTheDocument();
    const startLinks = screen.getAllByRole('link', { name: /Empezar hoy/ });
    expect(startLinks).toHaveLength(1);
    expect(startLinks[0]).toHaveAttribute('href', '/workouts/w1/session/day-today');
  });

  it('does not show Empezar hoy when the active workout has no plan day today', async () => {
    const otherDay = DAYS[(DAYS.indexOf(TODAY_KEY) + 1) % 7];
    mockWorkouts([
      {
        ...ACTIVE_WORKOUT,
        training_days: [
          { ...ACTIVE_WORKOUT.training_days[0], day_of_week: otherDay },
        ],
      },
    ]);
    renderWithProviders(<WorkoutsPage />);

    expect(await screen.findByText('Push Pull Legs')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Empezar hoy/ })).not.toBeInTheDocument();
  });

  it('opens the NewRoutineModal when clicking Nueva rutina', async () => {
    const user = userEvent.setup();
    mockWorkouts([ACTIVE_WORKOUT]);
    renderWithProviders(<WorkoutsPage />);

    expect(await screen.findByText('Push Pull Legs')).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /Nueva rutina/ }));

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByLabelText(/Nombre/)).toBeInTheDocument();
  });

  it('renders the empty state with a create CTA when there are no workouts', async () => {
    mockWorkouts([]);
    renderWithProviders(<WorkoutsPage />);

    expect(await screen.findByText(/Sin rutinas todavía/)).toBeInTheDocument();
  });
});
