import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Route, Routes } from 'react-router-dom';
import { renderWithProviders } from '../test/test-utils';
import { WorkoutDetailPage } from './WorkoutDetailPage';
import { ApiError } from '../lib/api';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../lib/api';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

const WORKOUT_FIXTURE = {
  id: 'w1',
  name: 'Mi Rutina',
  description: null,
  is_active: true,
  training_days: [
    {
      id: 'day-mon',
      day_of_week: 'MONDAY',
      order: 0,
      exercises: [],
    },
    {
      id: 'day-wed',
      day_of_week: 'WEDNESDAY',
      order: 1,
      exercises: [],
    },
  ],
};

const WORKOUT_ZERO_DAYS = {
  ...WORKOUT_FIXTURE,
  training_days: [],
};

function makeApiFetchHandler(overrides: Record<string, unknown> = {}) {
  return (path: string, options?: RequestInit) => {
    const method = options?.method ?? 'GET';

    if (path === '/workouts/w1' && method === 'GET') {
      return Promise.resolve(overrides['/workouts/w1'] ?? WORKOUT_FIXTURE);
    }

    if (path === '/exercises' && method === 'GET') {
      return Promise.resolve([]);
    }

    if (path.startsWith('/workouts/w1/days/') && path.endsWith('/sessions') && method === 'GET') {
      return Promise.resolve([]);
    }

    if (path === '/workouts/w1/training-days' && method === 'POST') {
      if (overrides['POST /workouts/w1/training-days'] !== undefined) {
        const override = overrides['POST /workouts/w1/training-days'];
        if (override instanceof Error) return Promise.reject(override);
        return Promise.resolve(override);
      }
      return Promise.resolve(undefined);
    }

    if (path.startsWith('/workouts/w1/training-days/') && method === 'DELETE') {
      const day = path.split('/workouts/w1/training-days/')[1];
      const key = `DELETE /workouts/w1/training-days/${day}`;
      if (overrides[key] !== undefined) {
        const override = overrides[key];
        if (override instanceof Error) return Promise.reject(override);
        return Promise.resolve(override);
      }
      return Promise.resolve(undefined);
    }

    if (path.startsWith('/workouts/w1') && method === 'PATCH') {
      return Promise.resolve(overrides[`PATCH ${path}`] ?? WORKOUT_FIXTURE);
    }

    return Promise.resolve(undefined);
  };
}

function renderPage(workoutOverride?: Partial<typeof WORKOUT_FIXTURE>) {
  const fixture = workoutOverride
    ? { ...WORKOUT_FIXTURE, ...workoutOverride }
    : WORKOUT_FIXTURE;
  mockApiFetch.mockImplementation(makeApiFetchHandler({ '/workouts/w1': fixture }));

  return renderWithProviders(
    <Routes>
      <Route path="/workouts/:id" element={<WorkoutDetailPage />} />
    </Routes>,
    ['/workouts/w1'],
  );
}

afterEach(() => {
  vi.clearAllMocks();
});

describe('add training day (day chip picker)', () => {
  it('opens the picker with only days not already in the workout', async () => {
    renderPage();

    await screen.findByText('Mi Rutina');

    const addBtn = screen.getByRole('button', { name: '+ Agregar día' });
    await userEvent.click(addBtn);

    expect(screen.queryByRole('button', { name: 'Lunes' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Miércoles' })).not.toBeInTheDocument();

    expect(screen.getByRole('button', { name: 'Martes' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Jueves' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Viernes' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sábado' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Domingo' })).toBeInTheDocument();
  });

  it('POSTs /workouts/w1/training-days with { day_of_week: "FRIDAY" } and closes picker on success', async () => {
    mockApiFetch.mockImplementation(
      makeApiFetchHandler({
        '/workouts/w1': WORKOUT_FIXTURE,
        'POST /workouts/w1/training-days': undefined,
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/workouts/:id" element={<WorkoutDetailPage />} />
      </Routes>,
      ['/workouts/w1'],
    );

    await screen.findByText('Mi Rutina');

    await userEvent.click(screen.getByRole('button', { name: '+ Agregar día' }));
    await userEvent.click(screen.getByRole('button', { name: 'Viernes' }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        '/workouts/w1/training-days',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ day_of_week: 'FRIDAY' }),
        }),
      );
    });

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: 'Viernes' })).not.toBeInTheDocument();
    });
  });

  it('shows API error when adding a day fails, picker stays open', async () => {
    mockApiFetch.mockImplementation(
      makeApiFetchHandler({
        '/workouts/w1': WORKOUT_FIXTURE,
        'POST /workouts/w1/training-days': new ApiError('Día no válido', 400),
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/workouts/:id" element={<WorkoutDetailPage />} />
      </Routes>,
      ['/workouts/w1'],
    );

    await screen.findByText('Mi Rutina');

    await userEvent.click(screen.getByRole('button', { name: '+ Agregar día' }));
    await userEvent.click(screen.getByRole('button', { name: 'Viernes' }));

    await screen.findByText('Día no válido');

    expect(screen.getByRole('button', { name: 'Viernes' })).toBeInTheDocument();
  });

  it('shows empty-state with full 7-day chip list when workout has zero training days', async () => {
    mockApiFetch.mockImplementation(
      makeApiFetchHandler({ '/workouts/w1': WORKOUT_ZERO_DAYS }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/workouts/:id" element={<WorkoutDetailPage />} />
      </Routes>,
      ['/workouts/w1'],
    );

    await screen.findByText('Sin días de entrenamiento configurados.');

    const allDayLabels = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    for (const label of allDayLabels) {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument();
    }
  });
});

describe('remove training day (TrainingDayCard)', () => {
  it('trash button shows inline confirmation; "Cancelar" dismisses without DELETE request', async () => {
    renderPage();

    await screen.findByText('Lunes');

    const mondayCard = screen.getByText('Lunes').closest('div.rounded-card') as HTMLElement;
    const trashBtn = within(mondayCard).getByRole('button', { name: 'Eliminar día' });
    await userEvent.click(trashBtn);

    expect(await screen.findByText('Sí, eliminar')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }));

    expect(screen.queryByText('Sí, eliminar')).not.toBeInTheDocument();

    const deleteCalls = mockApiFetch.mock.calls.filter(
      (args: unknown[]) => {
        const [path, opts] = args as [string, RequestInit?];
        return path.includes('training-days') && opts?.method === 'DELETE';
      },
    );
    expect(deleteCalls).toHaveLength(0);
  });

  it('"Sí, eliminar" DELETEs /workouts/w1/training-days/MONDAY', async () => {
    renderPage();

    await screen.findByText('Lunes');

    const mondayCard = screen.getByText('Lunes').closest('div.rounded-card') as HTMLElement;
    await userEvent.click(within(mondayCard).getByRole('button', { name: 'Eliminar día' }));
    await userEvent.click(await screen.findByRole('button', { name: 'Sí, eliminar' }));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        '/workouts/w1/training-days/MONDAY',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });
  });

  it('shows the API error message when day removal fails', async () => {
    mockApiFetch.mockImplementation((path: string, options?: RequestInit) => {
      const method = options?.method ?? 'GET';

      if (path === '/workouts/w1' && method === 'GET') return Promise.resolve(WORKOUT_FIXTURE);
      if (path === '/exercises') return Promise.resolve([]);
      if (path.startsWith('/workouts/w1/days/') && path.endsWith('/sessions')) return Promise.resolve([]);

      if (path === '/workouts/w1/training-days/MONDAY' && method === 'DELETE') {
        return Promise.reject(
          new ApiError('No se pudo eliminar el día. Inténtalo de nuevo.', 500),
        );
      }

      return Promise.resolve(undefined);
    });

    renderWithProviders(
      <Routes>
        <Route path="/workouts/:id" element={<WorkoutDetailPage />} />
      </Routes>,
      ['/workouts/w1'],
    );

    await screen.findByText('Lunes');

    const mondayCard = screen.getByText('Lunes').closest('div.rounded-card') as HTMLElement;
    await userEvent.click(within(mondayCard).getByRole('button', { name: 'Eliminar día' }));
    await userEvent.click(await screen.findByRole('button', { name: 'Sí, eliminar' }));

    await screen.findByText('No se pudo eliminar el día. Inténtalo de nuevo.');
  });
});

describe('rename workout', () => {
  it('shows error and sends no request when committing empty/whitespace name', async () => {
    renderPage();

    await screen.findByText('Mi Rutina');

    await userEvent.click(screen.getByRole('button', { name: 'Renombrar entrenamiento' }));

    const input = screen.getByRole('textbox', { name: 'Nuevo nombre del entrenamiento' });
    await userEvent.clear(input);
    await userEvent.type(input, '   ');

    const callsBefore = mockApiFetch.mock.calls.length;
    await userEvent.keyboard('{Enter}');

    expect(await screen.findByText('El nombre no puede estar vacío.')).toBeInTheDocument();
    expect(mockApiFetch.mock.calls.length).toBe(callsBefore);
  });

  it('Escape cancels rename and restores the heading', async () => {
    renderPage();

    await screen.findByText('Mi Rutina');

    await userEvent.click(screen.getByRole('button', { name: 'Renombrar entrenamiento' }));

    const input = screen.getByRole('textbox', { name: 'Nuevo nombre del entrenamiento' });
    await userEvent.clear(input);
    await userEvent.type(input, 'Nombre Nuevo');

    await userEvent.keyboard('{Escape}');

    expect(screen.queryByRole('textbox', { name: 'Nuevo nombre del entrenamiento' })).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Mi Rutina' })).toBeInTheDocument();
  });
});
