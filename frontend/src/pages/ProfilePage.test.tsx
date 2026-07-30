import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/test-utils';
import { ProfilePage } from './ProfilePage';
import { useAuthStore } from '../store/authStore';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../lib/api';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

const STATS_FIXTURE = {
  total_sessions: 10,
  streak: 3,
  total_prs: 5,
  weekly_volume_kg: 800,
  weekly_sessions: 2,
  weekly_prs: 1,
};

const PREFS_FIXTURE = {
  id: 'u1',
  email: 'federico@example.com',
  created_at: '2026-01-01T00:00:00Z',
  rest_seconds: 90,
  units: 'kg' as const,
};

function mockApi(overrides: {
  stats?: typeof STATS_FIXTURE;
  prefs?: typeof PREFS_FIXTURE;
} = {}) {
  mockApiFetch.mockImplementation((path: string) => {
    if (path === '/users/me/stats') {
      return Promise.resolve(overrides.stats ?? STATS_FIXTURE);
    }
    if (path === '/auth/me') {
      return Promise.resolve(overrides.prefs ?? PREFS_FIXTURE);
    }
    if (path === '/users/me/preferences') {
      return Promise.resolve(overrides.prefs ?? PREFS_FIXTURE);
    }
    if (path.startsWith('/workouts')) {
      return Promise.resolve([]);
    }
    return Promise.resolve(undefined);
  });
}

beforeEach(() => {
  useAuthStore.setState({
    token: 'token',
    user: { id: 'u1', email: 'federico@example.com', created_at: '2026-01-01T00:00:00Z', rest_seconds: 90, units: 'kg' as const },
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('ProfilePage', () => {
  it('renders the stats bar with sessions, streak, and PRs from useUserStats', async () => {
    mockApi();
    renderWithProviders(<ProfilePage />);

    expect(await screen.findByText('10')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('Sesiones')).toBeInTheDocument();
    expect(screen.getByText('Racha')).toBeInTheDocument();
    expect(screen.getByText('PRs')).toBeInTheDocument();
  });

  it('renders the rest_seconds value from useUserPreferences', async () => {
    mockApi();
    renderWithProviders(<ProfilePage />);

    // The rest button shows "M:SS (Ns)" format — e.g. "1:30 (90s)"
    expect(await screen.findByText(/90s/)).toBeInTheDocument();
  });

  it('editing rest seconds and blurring calls PATCH /users/me/preferences', async () => {
    const user = userEvent.setup();
    mockApi();
    renderWithProviders(<ProfilePage />);

    // Click the rest button to enter edit mode
    const restBtn = await screen.findByRole('button', { name: /Editar tiempo de descanso/ });
    await user.click(restBtn);

    // The input should now be visible
    const input = screen.getByRole('spinbutton', { name: /Segundos de descanso/ });
    await user.clear(input);
    await user.type(input, '120');
    await user.tab(); // blur triggers commitRestEdit

    expect(mockApiFetch).toHaveBeenCalledWith(
      '/users/me/preferences',
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ rest_seconds: 120 }),
      }),
    );
  });
});
