import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/test-utils';
import { LoginPage } from './LoginPage';
import { useAuthStore } from '../store/authStore';

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
import { useNavigate } from 'react-router-dom';

const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;
const mockUseNavigate = useNavigate as ReturnType<typeof vi.fn>;

const MOCK_TOKEN = { access_token: 'tok123', token_type: 'bearer' };
const MOCK_USER = {
  id: 'u1',
  email: 'test@example.com',
  created_at: '2024-01-01T00:00:00Z',
  rest_seconds: 90,
  units: 'kg' as const,
};

afterEach(() => {
  vi.clearAllMocks();
  useAuthStore.setState({ token: null, user: null });
});

describe('LoginPage', () => {
  it('renders email input, password input, and submit button', () => {
    renderWithProviders(<LoginPage />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument();
  });

  it('successful login — calls apiFetch twice, updates store, and navigates to /dashboard', async () => {
    const mockNavigate = vi.fn();
    mockUseNavigate.mockReturnValue(mockNavigate);

    mockApiFetch
      .mockResolvedValueOnce(MOCK_TOKEN)  // POST /auth/login
      .mockResolvedValueOnce(MOCK_USER);  // GET /auth/me

    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/contraseña/i), 'mypassword');
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/dashboard'));

    expect(mockApiFetch).toHaveBeenCalledTimes(2);
    expect(mockApiFetch).toHaveBeenNthCalledWith(
      1,
      '/auth/login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'test@example.com', password: 'mypassword' }),
      }),
    );

    const state = useAuthStore.getState();
    expect(state.token).toBe('tok123');
    expect(state.user).toEqual(MOCK_USER);
  });

  it('invalid credentials (401) — shows error message and does not navigate', async () => {
    const mockNavigate = vi.fn();
    mockUseNavigate.mockReturnValue(mockNavigate);

    const { ApiError } = await import('../lib/api');
    mockApiFetch.mockRejectedValueOnce(new ApiError('Credenciales inválidas', 401));

    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    await user.type(screen.getByLabelText(/email/i), 'bad@example.com');
    await user.type(screen.getByLabelText(/contraseña/i), 'wrongpass');
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

    await screen.findByText('Credenciales inválidas');

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('validation — empty email shows Zod error, no API call made', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    // Type only password, leave email empty
    await user.type(screen.getByLabelText(/contraseña/i), 'somepassword');
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

    await screen.findByText('Email inválido');
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it('validation — empty password shows Zod error, no API call made', async () => {
    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

    await screen.findByText('La contraseña es requerida');
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it('loading state — button is disabled and shows loading text while request is in flight', async () => {
    const mockNavigate = vi.fn();
    mockUseNavigate.mockReturnValue(mockNavigate);

    let resolveLogin!: (v: unknown) => void;
    mockApiFetch.mockReturnValueOnce(new Promise((resolve) => { resolveLogin = resolve; }));

    const user = userEvent.setup();
    renderWithProviders(<LoginPage />);

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/contraseña/i), 'mypassword');
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }));

    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /iniciando/i });
      expect(btn).toBeDisabled();
    });

    // Resolve to avoid dangling promises
    resolveLogin(MOCK_TOKEN);
  });

  it('link to register — register link is present with correct href', () => {
    renderWithProviders(<LoginPage />);

    const link = screen.getByRole('link', { name: /regístrate/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/register');
  });

  it('link to forgot password — forgot password link is present', () => {
    renderWithProviders(<LoginPage />);

    const link = screen.getByRole('link', { name: /olvidaste tu contraseña/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/forgot-password');
  });
});
