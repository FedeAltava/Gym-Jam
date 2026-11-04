import { screen, within, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/test-utils';
import { BodyWeightCard } from './BodyWeightCard';

vi.mock('../../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../../lib/api';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

const HISTORY = [
  { measured_on: '2026-11-04', weight_kg: 84.2 },
  { measured_on: '2026-11-01', weight_kg: 84.7 },
  { measured_on: '2026-10-28', weight_kg: 85.0 },
];

function mockHistory(history: unknown[] = HISTORY) {
  mockApiFetch.mockImplementation((path: string, options?: RequestInit) => {
    if (path === '/users/me/body-weight') return Promise.resolve(history);
    if (options?.method === 'PUT') {
      const measured_on = path.split('/').pop();
      return Promise.resolve({ measured_on, ...JSON.parse(options.body as string) });
    }
    return Promise.resolve(undefined);
  });
}

function todayIso(): string {
  const d = new Date();
  return [d.getFullYear(), String(d.getMonth() + 1).padStart(2, '0'), String(d.getDate()).padStart(2, '0')].join('-');
}

afterEach(() => {
  vi.clearAllMocks();
});

describe('BodyWeightCard', () => {
  it('shows the latest weight and the history newest first with the change against the previous entry', async () => {
    mockHistory();
    renderWithProviders(<BodyWeightCard />);

    expect(await screen.findByLabelText('Último peso')).toHaveTextContent('84,2 kg');
    const rows = within(screen.getByRole('list', { name: 'Histórico de peso' })).getAllByRole('listitem');
    expect(rows).toHaveLength(3);
    expect(rows[0]).toHaveTextContent('4 nov 2026');
    expect(rows[0]).toHaveTextContent('84,2 kg');
    expect(rows[0]).toHaveTextContent('-0,5 kg');
    expect(rows[1]).toHaveTextContent('1 nov 2026');
    expect(rows[1]).toHaveTextContent('-0,3 kg');
    // The oldest entry has nothing to compare with.
    expect(rows[2]).toHaveTextContent('28 oct 2026');
    expect(rows[2]).not.toHaveTextContent(/[+-]\d/);
  });

  it('shows an empty state when no weight is recorded yet', async () => {
    mockHistory([]);
    renderWithProviders(<BodyWeightCard />);

    expect(await screen.findByText('Aún no has registrado tu peso.')).toBeInTheDocument();
    expect(screen.queryByRole('list', { name: 'Histórico de peso' })).not.toBeInTheDocument();
  });

  it("saves today's weight by default and accepts a decimal comma", async () => {
    mockHistory();
    const user = userEvent.setup();
    renderWithProviders(<BodyWeightCard />);
    await screen.findByLabelText('Último peso');

    expect(screen.getByLabelText('Fecha')).toHaveValue(todayIso());
    await user.type(screen.getByLabelText('Peso (kg)'), '84,5');
    await user.click(screen.getByRole('button', { name: 'Guardar peso' }));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith(`/users/me/body-weight/${todayIso()}`, {
        method: 'PUT',
        body: JSON.stringify({ weight_kg: 84.5 }),
      }),
    );
    await waitFor(() => expect(screen.getByLabelText('Peso (kg)')).toHaveValue(''));
  });

  it('saves the weight for another chosen day', async () => {
    mockHistory();
    const user = userEvent.setup();
    renderWithProviders(<BodyWeightCard />);
    await screen.findByLabelText('Último peso');

    fireEvent.change(screen.getByLabelText('Fecha'), { target: { value: '2026-10-30' } });
    await user.type(screen.getByLabelText('Peso (kg)'), '84.9');
    await user.click(screen.getByRole('button', { name: 'Guardar peso' }));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith('/users/me/body-weight/2026-10-30', {
        method: 'PUT',
        body: JSON.stringify({ weight_kg: 84.9 }),
      }),
    );
  });

  it('warns that saving replaces the weight already recorded that day', async () => {
    mockHistory();
    renderWithProviders(<BodyWeightCard />);
    await screen.findByLabelText('Último peso');

    fireEvent.change(screen.getByLabelText('Fecha'), { target: { value: '2026-11-01' } });

    expect(screen.getByText('Ese día ya tiene 84,7 kg; se sustituirá.')).toBeInTheDocument();
  });

  it('rejects an invalid weight without calling the API', async () => {
    mockHistory();
    const user = userEvent.setup();
    renderWithProviders(<BodyWeightCard />);
    await screen.findByLabelText('Último peso');

    for (const value of ['0', 'abc', '401']) {
      await user.clear(screen.getByLabelText('Peso (kg)'));
      await user.type(screen.getByLabelText('Peso (kg)'), value);
      await user.click(screen.getByRole('button', { name: 'Guardar peso' }));
      expect(screen.getByText('Introduce un peso mayor que 0 y de hasta 400 kg.')).toBeInTheDocument();
    }
    expect(mockApiFetch).not.toHaveBeenCalledWith(expect.stringMatching(/^\/users\/me\/body-weight\//), expect.anything());
  });

  it('deletes an entry from the history', async () => {
    mockHistory();
    const user = userEvent.setup();
    renderWithProviders(<BodyWeightCard />);
    await screen.findByLabelText('Último peso');

    await user.click(screen.getByRole('button', { name: 'Borrar el peso del 1 nov 2026' }));

    await waitFor(() =>
      expect(mockApiFetch).toHaveBeenCalledWith('/users/me/body-weight/2026-11-01', { method: 'DELETE' }),
    );
  });
});
