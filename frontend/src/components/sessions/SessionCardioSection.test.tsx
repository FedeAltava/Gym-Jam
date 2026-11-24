import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/test-utils';
import { SessionCardioSection } from './SessionCardioSection';

vi.mock('../../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../../lib/api';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

const ENTRY = {
  id: 'c1',
  duration_minutes: 20,
  distance_km: 2.5,
  speed_kmh: 7.5,
  incline_percent: 3.5,
  calories: 250,
};

function renderSection(entries = [ENTRY]) {
  const user = userEvent.setup();
  const { queryClient } = renderWithProviders(<SessionCardioSection sessionId="sess1" entries={entries} />);
  return { user, queryClient };
}

describe('SessionCardioSection', () => {
  beforeEach(() => {
    mockApiFetch.mockReset();
  });

  it('lists the recorded treadmill cardio', () => {
    renderSection();

    const section = screen.getByRole('region', { name: 'Cardio en cinta' });
    expect(within(section).getByText('20 min · 2,5 km · 7,5 km/h · pendiente 3,5 % · 250 kcal')).toBeInTheDocument();
  });

  it('shows only the add button when nothing was recorded', () => {
    renderSection([]);

    expect(screen.getByRole('button', { name: 'Añadir cardio' })).toBeInTheDocument();
    expect(screen.queryByRole('list', { name: 'Cardio registrado' })).not.toBeInTheDocument();
  });

  it('adds cardio with the filled values and refreshes the sessions', async () => {
    mockApiFetch.mockResolvedValue({ ...ENTRY, id: 'c2' });
    const { user, queryClient } = renderSection([]);
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');

    await user.click(screen.getByRole('button', { name: 'Añadir cardio' }));
    const dialog = screen.getByRole('dialog', { name: 'Añadir cardio' });
    await user.type(within(dialog).getByLabelText('Minutos'), '25');
    await user.type(within(dialog).getByLabelText('Distancia (km)'), '3,2');
    await user.type(within(dialog).getByLabelText('Pendiente (%)'), '0');
    await user.click(within(dialog).getByRole('button', { name: 'Guardar' }));

    expect(mockApiFetch).toHaveBeenCalledWith('/sessions/sess1/cardio', {
      method: 'POST',
      body: JSON.stringify({
        duration_minutes: 25,
        distance_km: 3.2,
        speed_kmh: null,
        incline_percent: 0,
        calories: null,
      }),
    });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['sessions'] });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('does not send an empty or invalid form', async () => {
    const { user } = renderSection([]);

    await user.click(screen.getByRole('button', { name: 'Añadir cardio' }));
    const dialog = screen.getByRole('dialog', { name: 'Añadir cardio' });
    await user.click(within(dialog).getByRole('button', { name: 'Guardar' }));
    expect(within(dialog).getByText('Rellena al menos un campo.')).toBeInTheDocument();

    await user.type(within(dialog).getByLabelText('Pendiente (%)'), '41');
    await user.click(within(dialog).getByRole('button', { name: 'Guardar' }));
    expect(within(dialog).getByText('La pendiente debe estar entre 0 y 40 %.')).toBeInTheDocument();

    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it('keeps the sheet open with an error when saving fails', async () => {
    mockApiFetch.mockImplementation(() => Promise.reject(new Error('boom')));
    const { user } = renderSection([]);

    await user.click(screen.getByRole('button', { name: 'Añadir cardio' }));
    const dialog = screen.getByRole('dialog', { name: 'Añadir cardio' });
    await user.type(within(dialog).getByLabelText('Calorías (kcal)'), '300');
    await user.click(within(dialog).getByRole('button', { name: 'Guardar' }));

    expect(await within(dialog).findByText('No se pudo guardar el cardio. Inténtalo de nuevo.')).toBeInTheDocument();
    expect(within(dialog).getByLabelText('Calorías (kcal)')).toHaveValue('300');
  });

  it('deletes an entry and refreshes the sessions', async () => {
    mockApiFetch.mockResolvedValue(undefined);
    const { user, queryClient } = renderSection();
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');

    await user.click(
      screen.getByRole('button', { name: 'Borrar cardio 20 min · 2,5 km · 7,5 km/h · pendiente 3,5 % · 250 kcal' }),
    );

    expect(mockApiFetch).toHaveBeenCalledWith('/sessions/sess1/cardio/c1', { method: 'DELETE' });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['sessions'] });
  });

  it('shows an error when deleting fails', async () => {
    mockApiFetch.mockImplementation(() => Promise.reject(new Error('boom')));
    const { user } = renderSection();

    await user.click(screen.getByRole('button', { name: /^Borrar cardio/ }));

    expect(await screen.findByText('No se pudo borrar el cardio. Inténtalo de nuevo.')).toBeInTheDocument();
  });
});
