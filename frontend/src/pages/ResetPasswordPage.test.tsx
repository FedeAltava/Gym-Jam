import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/test-utils';
import { ResetPasswordPage } from './ResetPasswordPage';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

// vi.hoisted ensures the variable is initialised before the hoisted vi.mock factory runs.
const mockUseSearchParams = vi.hoisted(() => vi.fn());
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: vi.fn(() => vi.fn()),
    useSearchParams: mockUseSearchParams,
  };
});

import { apiFetch } from '../lib/api';

const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

/** Helper to set the ?token= query param for a test. */
function withToken(token: string) {
  mockUseSearchParams.mockReturnValue([new URLSearchParams({ token }), vi.fn()]);
}

/** No token in the URL. */
function withoutToken() {
  mockUseSearchParams.mockReturnValue([new URLSearchParams(), vi.fn()]);
}

afterEach(() => {
  vi.clearAllMocks();
});

describe('ResetPasswordPage', () => {
  it('renders new password and confirm password fields', () => {
    withToken('valid-token');
    renderWithProviders(<ResetPasswordPage />);

    expect(screen.getByLabelText(/nueva contraseña/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirmar contraseña/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cambiar contraseña/i })).toBeInTheDocument();
  });

  it('successful reset — calls apiFetch with token + new_password, shows success message', async () => {
    withToken('my-valid-token');
    mockApiFetch.mockResolvedValueOnce(undefined); // 204

    const user = userEvent.setup();
    renderWithProviders(<ResetPasswordPage />);

    await user.type(screen.getByLabelText(/nueva contraseña/i), 'newsecurepass');
    await user.type(screen.getByLabelText(/confirmar contraseña/i), 'newsecurepass');
    await user.click(screen.getByRole('button', { name: /cambiar contraseña/i }));

    await screen.findByText(/contraseña actualizada/i);

    expect(mockApiFetch).toHaveBeenCalledTimes(1);
    expect(mockApiFetch).toHaveBeenCalledWith(
      '/auth/reset-password',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ token: 'my-valid-token', new_password: 'newsecurepass' }),
      }),
    );
  });

  it('password too short — minLength is browser-enforced; jsdom does not block submit, API is called', async () => {
    // ResetPasswordPage enforces minimum length via the HTML minLength={8} attribute only.
    // Real browsers block the submit event, but jsdom does not enforce minLength during
    // programmatic submission. This test documents the actual jsdom behavior and verifies
    // the API is reached (real protection lives in the backend and the browser).
    withToken('valid-token');

    const { ApiError } = await import('../lib/api');
    mockApiFetch.mockRejectedValueOnce(new ApiError('Password too short', 422));

    const user = userEvent.setup();
    renderWithProviders(<ResetPasswordPage />);

    await user.type(screen.getByLabelText(/nueva contraseña/i), 'short');
    await user.type(screen.getByLabelText(/confirmar contraseña/i), 'short');
    await user.click(screen.getByRole('button', { name: /cambiar contraseña/i }));

    // jsdom does not block — API is called, backend rejects, error is shown
    await screen.findByText(/el enlace es inválido o ya expiró/i);
    expect(mockApiFetch).toHaveBeenCalledTimes(1);
  });

  it('passwords do not match — JS validation error shown before API call', async () => {
    withToken('valid-token');

    const user = userEvent.setup();
    renderWithProviders(<ResetPasswordPage />);

    await user.type(screen.getByLabelText(/nueva contraseña/i), 'password123');
    await user.type(screen.getByLabelText(/confirmar contraseña/i), 'different456');
    await user.click(screen.getByRole('button', { name: /cambiar contraseña/i }));

    await screen.findByText(/las contraseñas no coinciden/i);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it('invalid/expired token (400) — API error shown, success screen not rendered', async () => {
    withToken('expired-or-invalid-token');

    const { ApiError } = await import('../lib/api');
    mockApiFetch.mockRejectedValueOnce(new ApiError('Token inválido', 400));

    const user = userEvent.setup();
    renderWithProviders(<ResetPasswordPage />);

    await user.type(screen.getByLabelText(/nueva contraseña/i), 'newpassword');
    await user.type(screen.getByLabelText(/confirmar contraseña/i), 'newpassword');
    await user.click(screen.getByRole('button', { name: /cambiar contraseña/i }));

    await screen.findByText(/el enlace es inválido o ya expiró/i);
    expect(screen.queryByText(/contraseña actualizada/i)).not.toBeInTheDocument();
  });

  it('missing token — submitting calls API with empty token, then shows error on failure', async () => {
    // The component reads token = searchParams.get('token') ?? ''
    // With no token param, token is ''. The mutation is still attempted.
    withoutToken();

    const { ApiError } = await import('../lib/api');
    mockApiFetch.mockRejectedValueOnce(new ApiError('Token requerido', 422));

    const user = userEvent.setup();
    renderWithProviders(<ResetPasswordPage />);

    await user.type(screen.getByLabelText(/nueva contraseña/i), 'newpassword');
    await user.type(screen.getByLabelText(/confirmar contraseña/i), 'newpassword');
    await user.click(screen.getByRole('button', { name: /cambiar contraseña/i }));

    await screen.findByText(/el enlace es inválido o ya expiró/i);

    expect(mockApiFetch).toHaveBeenCalledWith(
      '/auth/reset-password',
      expect.objectContaining({
        body: JSON.stringify({ token: '', new_password: 'newpassword' }),
      }),
    );
  });

  it('loading state — button disabled and shows loading text while pending', async () => {
    withToken('valid-token');

    let resolveMutation!: (v: unknown) => void;
    mockApiFetch.mockReturnValueOnce(
      new Promise((resolve) => { resolveMutation = resolve; }),
    );

    const user = userEvent.setup();
    renderWithProviders(<ResetPasswordPage />);

    await user.type(screen.getByLabelText(/nueva contraseña/i), 'newsecurepass');
    await user.type(screen.getByLabelText(/confirmar contraseña/i), 'newsecurepass');
    await user.click(screen.getByRole('button', { name: /cambiar contraseña/i }));

    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /guardando/i });
      expect(btn).toBeDisabled();
    });

    // Resolve to avoid dangling promises
    resolveMutation(undefined);
  });
});
