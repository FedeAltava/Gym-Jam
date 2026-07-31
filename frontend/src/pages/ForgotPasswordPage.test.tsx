import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/test-utils';
import { ForgotPasswordPage } from './ForgotPasswordPage';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: vi.fn(() => vi.fn()),
  };
});

import { apiFetch } from '../lib/api';

const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

afterEach(() => {
  vi.clearAllMocks();
});

describe('ForgotPasswordPage', () => {
  it('renders a single email input and submit button', () => {
    renderWithProviders(<ForgotPasswordPage />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /enviar enlace/i })).toBeInTheDocument();
  });

  it('successful submission — calls apiFetch with the email and shows success message', async () => {
    mockApiFetch.mockResolvedValueOnce(undefined); // 204 No Content

    const user = userEvent.setup();
    renderWithProviders(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/email/i), 'user@example.com');
    await user.click(screen.getByRole('button', { name: /enviar enlace/i }));

    await screen.findByText(/si tu email está registrado/i);

    expect(mockApiFetch).toHaveBeenCalledTimes(1);
    expect(mockApiFetch).toHaveBeenCalledWith(
      '/auth/forgot-password',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'user@example.com' }),
      }),
    );
  });

  it('non-existent email — backend always returns 204, success message is shown (security)', async () => {
    // Backend responds 204 regardless of whether email exists.
    // From the UI perspective this is identical to a real success.
    mockApiFetch.mockResolvedValueOnce(undefined);

    const user = userEvent.setup();
    renderWithProviders(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/email/i), 'ghost@nowhere.com');
    await user.click(screen.getByRole('button', { name: /enviar enlace/i }));

    await screen.findByText(/si tu email está registrado/i);
  });

  it('invalid email format — native browser validation prevents submit, apiFetch not called', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ForgotPasswordPage />);

    // Enter a value that fails the email type validator (no @ symbol)
    await user.type(screen.getByLabelText(/email/i), 'notanemail');
    await user.click(screen.getByRole('button', { name: /enviar enlace/i }));

    // Success screen must not appear and API must not be called
    expect(screen.queryByText(/si tu email está registrado/i)).not.toBeInTheDocument();
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it('API error — shows generic error message, success screen not shown', async () => {
    const { ApiError } = await import('../lib/api');
    mockApiFetch.mockRejectedValueOnce(new ApiError('Server error', 500));

    const user = userEvent.setup();
    renderWithProviders(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/email/i), 'user@example.com');
    await user.click(screen.getByRole('button', { name: /enviar enlace/i }));

    await screen.findByText(/ocurrió un error/i);
    expect(screen.queryByText(/si tu email está registrado/i)).not.toBeInTheDocument();
  });

  it('loading state — button is disabled and shows loading text while pending', async () => {
    let resolveMutation!: (v: unknown) => void;
    mockApiFetch.mockReturnValueOnce(
      new Promise((resolve) => { resolveMutation = resolve; }),
    );

    const user = userEvent.setup();
    renderWithProviders(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/email/i), 'user@example.com');
    await user.click(screen.getByRole('button', { name: /enviar enlace/i }));

    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /enviando/i });
      expect(btn).toBeDisabled();
    });

    // Resolve to avoid dangling promises
    resolveMutation(undefined);
  });
});
