import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/test-utils';
import { UploadMenuForm } from './UploadMenuForm';
import type { DietPlan } from '../../types/api';

vi.mock('../../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../../lib/api';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

afterEach(() => {
  vi.clearAllMocks();
});

const CREATED_PLAN: DietPlan = {
  id: 'plan1',
  user_id: 'u1',
  title: 'Mi Plan',
  calories: 2000,
  menu_json: '{}',
  uploaded_at: '2026-09-08T00:00:00Z',
};

describe('UploadMenuForm', () => {
  it('renders idle state with drop zone text', () => {
    renderWithProviders(<UploadMenuForm onSuccess={vi.fn()} />);

    expect(screen.getByText('Sube el PDF de tu nutricionista')).toBeInTheDocument();
    expect(screen.getByText('Toca para elegir un archivo')).toBeInTheDocument();
  });

  it('transitions to picked state when a file is selected', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UploadMenuForm onSuccess={vi.fn()} />);

    const input = screen.getByRole('button', { name: /Toca para elegir/i })
      .closest('div')
      ?.querySelector('input[type="file"]') as HTMLInputElement
      ?? document.querySelector('input[type="file"]') as HTMLInputElement;

    const file = new File(['pdf content'], 'mi-plan.pdf', { type: 'application/pdf' });
    await user.upload(input, file);

    // Should show the file name and a Procesar PDF button
    expect(screen.getByText('mi-plan.pdf')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Procesar PDF/i })).toBeInTheDocument();
  });

  it('shows done state after successful upload and calls onSuccess', async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    mockApiFetch.mockResolvedValue(CREATED_PLAN);

    renderWithProviders(<UploadMenuForm onSuccess={onSuccess} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['pdf'], 'plan.pdf', { type: 'application/pdf' });
    await user.upload(input, file);

    await user.click(screen.getByRole('button', { name: /Procesar PDF/i }));

    await waitFor(() => {
      expect(screen.getByText('Tu menú semanal está listo')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /Ver menú/i })).toBeInTheDocument();
    expect(onSuccess).toHaveBeenCalledWith(CREATED_PLAN);
  });

  it('shows processing state while uploading', async () => {
    // Use a never-resolving promise to freeze at processing state
    let resolveFn!: (v: unknown) => void;
    const pending = new Promise((res) => { resolveFn = res; });
    mockApiFetch.mockReturnValue(pending);

    const user = userEvent.setup();
    renderWithProviders(<UploadMenuForm onSuccess={vi.fn()} />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['pdf'], 'plan.pdf', { type: 'application/pdf' });
    await user.upload(input, file);

    await user.click(screen.getByRole('button', { name: /Procesar PDF/i }));

    await waitFor(() => {
      expect(screen.getByText('Leyendo tu PDF...')).toBeInTheDocument();
    });

    // Cleanup: resolve the pending promise
    resolveFn(CREATED_PLAN);
  });
});
