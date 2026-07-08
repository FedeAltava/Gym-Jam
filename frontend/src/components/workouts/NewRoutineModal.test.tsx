import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/test-utils';
import { NewRoutineModal } from './NewRoutineModal';

vi.mock('../../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../../lib/api';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

const CREATED_WORKOUT = {
  id: 'w-new',
  name: 'Push Day',
  description: null,
  is_active: false,
  training_days: [
    { id: 'td1', day_of_week: 'MONDAY', order: 0, exercises: [] },
  ],
};

afterEach(() => {
  vi.clearAllMocks();
});

describe('NewRoutineModal', () => {
  it('renders the name input, description input and the 7 day chips', () => {
    renderWithProviders(<NewRoutineModal onClose={vi.fn()} />);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByLabelText(/Nombre/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Descripción/)).toBeInTheDocument();
    for (const day of [
      'Lunes',
      'Martes',
      'Miércoles',
      'Jueves',
      'Viernes',
      'Sábado',
      'Domingo',
    ]) {
      expect(screen.getByRole('button', { name: day })).toBeInTheDocument();
    }
    expect(screen.getByRole('button', { name: /Crear rutina/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cancelar/ })).toBeInTheDocument();
  });

  it('shows a validation error when submitting without a name', async () => {
    const user = userEvent.setup();
    renderWithProviders(<NewRoutineModal onClose={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: 'Lunes' }));
    await user.click(screen.getByRole('button', { name: /Crear rutina/ }));

    expect(await screen.findByText('El nombre es obligatorio')).toBeInTheDocument();
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it('shows a validation error when submitting without selecting any day', async () => {
    const user = userEvent.setup();
    renderWithProviders(<NewRoutineModal onClose={vi.fn()} />);

    await user.type(screen.getByLabelText(/Nombre/), 'Push Day');
    await user.click(screen.getByRole('button', { name: /Crear rutina/ }));

    expect(await screen.findByText('Selecciona al menos un día')).toBeInTheDocument();
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it('toggles day chips on and off', async () => {
    const user = userEvent.setup();
    renderWithProviders(<NewRoutineModal onClose={vi.fn()} />);

    const monday = screen.getByRole('button', { name: 'Lunes' });
    expect(monday).toHaveAttribute('aria-pressed', 'false');

    await user.click(monday);
    expect(monday).toHaveAttribute('aria-pressed', 'true');

    await user.click(monday);
    expect(monday).toHaveAttribute('aria-pressed', 'false');
  });

  it('creates the workout with the selected days and closes on success', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    mockApiFetch.mockResolvedValue(CREATED_WORKOUT);
    renderWithProviders(<NewRoutineModal onClose={onClose} />);

    await user.type(screen.getByLabelText(/Nombre/), 'Push Day');
    await user.type(screen.getByLabelText(/Descripción/), 'Pecho y tríceps');
    await user.click(screen.getByRole('button', { name: 'Lunes' }));
    await user.click(screen.getByRole('button', { name: 'Jueves' }));
    await user.click(screen.getByRole('button', { name: /Crear rutina/ }));

    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
    expect(mockApiFetch).toHaveBeenCalledWith(
      '/workouts',
      expect.objectContaining({ method: 'POST' }),
    );
    const [, options] = mockApiFetch.mock.calls[0];
    expect(JSON.parse((options as RequestInit).body as string)).toEqual({
      name: 'Push Day',
      description: 'Pecho y tríceps',
      training_days: ['MONDAY', 'THURSDAY'],
    });
  });

  it('shows an error message and stays open when the request fails', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    mockApiFetch.mockRejectedValue(new Error('Request failed'));
    renderWithProviders(<NewRoutineModal onClose={onClose} />);

    await user.type(screen.getByLabelText(/Nombre/), 'Push Day');
    await user.click(screen.getByRole('button', { name: 'Lunes' }));
    await user.click(screen.getByRole('button', { name: /Crear rutina/ }));

    expect(await screen.findByText('Request failed')).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('closes without creating anything when cancel is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderWithProviders(<NewRoutineModal onClose={onClose} />);

    await user.click(screen.getByRole('button', { name: /Cancelar/ }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });
});
