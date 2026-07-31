import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/test-utils';
import { RegisterPage } from './RegisterPage';
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

const MOCK_USER = {
  id: 'u1',
  email: 'newuser@example.com',
  created_at: '2024-01-01T00:00:00Z',
  rest_seconds: 90,
  units: 'kg' as const,
};

afterEach(() => {
  vi.clearAllMocks();
  useAuthStore.setState({ token: null, user: null });
});

describe('RegisterPage', () => {
  it('renders email, password, and confirm password fields', () => {
    renderWithProviders(<RegisterPage />);

    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^contraseña$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirmar contraseña/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /crear cuenta/i })).toBeInTheDocument();
  });

  it('successful registration — calls apiFetch with email+password and navigates to /login', async () => {
    const mockNavigate = vi.fn();
    mockUseNavigate.mockReturnValue(mockNavigate);

    mockApiFetch.mockResolvedValueOnce(MOCK_USER);

    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />);

    await user.type(screen.getByLabelText(/^email$/i), 'newuser@example.com');
    await user.type(screen.getByLabelText(/^contraseña$/i), 'securepass');
    await user.type(screen.getByLabelText(/confirmar contraseña/i), 'securepass');
    await user.click(screen.getByRole('button', { name: /crear cuenta/i }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/login'));

    expect(mockApiFetch).toHaveBeenCalledTimes(1);
    expect(mockApiFetch).toHaveBeenCalledWith(
      '/auth/register',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'newuser@example.com', password: 'securepass' }),
      }),
    );
  });

  it('password too short — Zod validation error shown, no API call', async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />);

    await user.type(screen.getByLabelText(/^email$/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^contraseña$/i), 'short');
    await user.type(screen.getByLabelText(/confirmar contraseña/i), 'short');
    await user.click(screen.getByRole('button', { name: /crear cuenta/i }));

    await screen.findByText('Mínimo 8 caracteres');
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it('passwords do not match — validation error shown, no API call', async () => {
    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />);

    await user.type(screen.getByLabelText(/^email$/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^contraseña$/i), 'password123');
    await user.type(screen.getByLabelText(/confirmar contraseña/i), 'different123');
    await user.click(screen.getByRole('button', { name: /crear cuenta/i }));

    await screen.findByText('Las contraseñas no coinciden');
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it('email already exists (409) — API error shown, no navigation', async () => {
    const mockNavigate = vi.fn();
    mockUseNavigate.mockReturnValue(mockNavigate);

    const { ApiError } = await import('../lib/api');
    mockApiFetch.mockRejectedValueOnce(
      new ApiError('El email ya está registrado', 409),
    );

    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />);

    await user.type(screen.getByLabelText(/^email$/i), 'existing@example.com');
    await user.type(screen.getByLabelText(/^contraseña$/i), 'password123');
    await user.type(screen.getByLabelText(/confirmar contraseña/i), 'password123');
    await user.click(screen.getByRole('button', { name: /crear cuenta/i }));

    await screen.findByText('El email ya está registrado');
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('loading state — button disabled and shows loading text while pending', async () => {
    const mockNavigate = vi.fn();
    mockUseNavigate.mockReturnValue(mockNavigate);

    let resolveRegister!: (v: unknown) => void;
    mockApiFetch.mockReturnValueOnce(
      new Promise((resolve) => { resolveRegister = resolve; }),
    );

    const user = userEvent.setup();
    renderWithProviders(<RegisterPage />);

    await user.type(screen.getByLabelText(/^email$/i), 'newuser@example.com');
    await user.type(screen.getByLabelText(/^contraseña$/i), 'securepass');
    await user.type(screen.getByLabelText(/confirmar contraseña/i), 'securepass');
    await user.click(screen.getByRole('button', { name: /crear cuenta/i }));

    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /creando/i });
      expect(btn).toBeDisabled();
    });

    // Resolve to avoid dangling promises
    resolveRegister(MOCK_USER);
  });

  it('link to login — login link is present with correct href', () => {
    renderWithProviders(<RegisterPage />);

    const link = screen.getByRole('link', { name: /iniciar sesión/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/login');
  });
});
