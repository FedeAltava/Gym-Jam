import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../test/test-utils';
import { NutritionPage } from './NutritionPage';
import { useAuthStore } from '../store/authStore';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../lib/api';
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

beforeEach(() => {
  useAuthStore.setState({
    token: 'test-token',
    user: {
      id: 'u1',
      email: 'test@example.com',
      created_at: '2026-01-01T00:00:00Z',
      rest_seconds: 90,
      units: 'kg' as const,
    },
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

const MENUS_FIXTURE = [
  {
    id: 'm1',
    user_id: 'u1',
    title: 'Plan Semana 1',
    calories: 2000,
    uploaded_at: '2026-09-01T00:00:00Z',
  },
  {
    id: 'm2',
    user_id: 'u1',
    title: 'Plan Semana 2',
    calories: 1800,
    uploaded_at: '2026-09-08T00:00:00Z',
  },
];

const MENU_DETAIL = {
  id: 'm1',
  user_id: 'u1',
  title: 'Plan Semana 1',
  calories: 2000,
  menu_json: {
    title: 'Plan Semana 1',
    calories: 2000,
    shared: {
      desayuno: [{ name: 'Opción A', ingredients: ['Leche'] }],
      almuerzo_options: [{ name: 'Ensalada', ingredients: ['Lechuga'] }],
      merienda: [{ name: 'Snack', ingredients: ['Manzana'] }],
    },
    days: [
      {
        day: 'Lunes',
        comida: { name: 'Pollo', ingredients: ['Pollo 150g'], is_free: false },
        cena: { name: 'Libre', ingredients: [], is_free: true },
      },
      {
        day: 'Martes',
        comida: { name: 'Ternera', ingredients: ['Ternera 200g'], is_free: false },
        cena: { name: 'Pescado', ingredients: ['Merluza'], is_free: false },
      },
      {
        day: 'Miércoles',
        comida: { name: 'Pasta', ingredients: ['Pasta'], is_free: false },
        cena: { name: 'Libre', ingredients: [], is_free: true },
      },
      {
        day: 'Jueves',
        comida: { name: 'Arroz', ingredients: ['Arroz'], is_free: false },
        cena: { name: 'Tortilla', ingredients: ['Huevos'], is_free: false },
      },
      {
        day: 'Viernes',
        comida: { name: 'Lentejas', ingredients: ['Lentejas'], is_free: false },
        cena: { name: 'Libre', ingredients: [], is_free: true },
      },
      {
        day: 'Sábado',
        comida: { name: 'Libre', ingredients: [], is_free: true },
        cena: { name: 'Libre', ingredients: [], is_free: true },
      },
      {
        day: 'Domingo',
        comida: { name: 'Paella', ingredients: ['Arroz', 'Marisco'], is_free: false },
        cena: { name: 'Libre', ingredients: [], is_free: true },
      },
    ],
  },
  uploaded_at: '2026-09-01T00:00:00Z',
};

function mockApi(overrides: { menus?: unknown; detail?: unknown } = {}) {
  mockApiFetch.mockImplementation((path: string) => {
    if (path === '/nutrition/menus') return Promise.resolve(overrides.menus ?? MENUS_FIXTURE);
    if (path.startsWith('/nutrition/menus/')) return Promise.resolve(overrides.detail ?? MENU_DETAIL);
    return Promise.resolve(undefined);
  });
}

describe('NutritionPage — list view', () => {
  it('shows the page title and subtitle', async () => {
    mockApi();
    renderWithProviders(<NutritionPage />);

    expect(screen.getByText('Nutrición')).toBeInTheDocument();
    expect(screen.getByText('Tus menús subidos')).toBeInTheDocument();
  });

  it('renders menu cards from the API', async () => {
    mockApi();
    renderWithProviders(<NutritionPage />);

    await waitFor(() => {
      expect(screen.getByText('Plan Semana 1')).toBeInTheDocument();
    });
    expect(screen.getByText('Plan Semana 2')).toBeInTheDocument();
  });
});

describe('NutritionPage — upload menu', () => {
  const NEW_MENU = {
    id: 'm3',
    user_id: 'u1',
    title: 'Plan Semana 3',
    calories: 1900,
    uploaded_at: '2026-09-15T00:00:00Z',
  };

  function pdfFile() {
    return new File(['%PDF-1.4'], 'menu.pdf', { type: 'application/pdf' });
  }

  // POST resolves/rejects only when the test says so, to observe the pending UI.
  function mockApiWithUpload(initialMenus: typeof MENUS_FIXTURE) {
    let menus = [...initialMenus];
    let settle: { resolve: () => void; reject: (e: Error) => void } | null = null;
    mockApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (init?.method === 'POST') {
        return new Promise((resolve, reject) => {
          settle = {
            resolve: () => {
              menus = [NEW_MENU, ...menus];
              resolve({ ...NEW_MENU, menu_json: MENU_DETAIL.menu_json });
            },
            reject,
          };
        });
      }
      if (path === '/nutrition/menus') return Promise.resolve(menus);
      return Promise.resolve(MENU_DETAIL);
    });
    return {
      resolveUpload: () => settle?.resolve(),
      rejectUpload: () => settle?.reject(new Error('boom')),
    };
  }

  const postCalls = () =>
    mockApiFetch.mock.calls.filter(([, init]) => (init as RequestInit | undefined)?.method === 'POST');

  it('opens the file picker from the CTA and uploads the chosen file without extra clicks', async () => {
    const user = userEvent.setup();
    mockApiWithUpload(MENUS_FIXTURE);
    renderWithProviders(<NutritionPage />);
    await screen.findByText('Plan Semana 1');

    const input = screen.getByLabelText('Archivo PDF del menú') as HTMLInputElement;
    const clickSpy = vi.spyOn(input, 'click');
    await user.click(screen.getByRole('button', { name: /Subir menú/i }));
    expect(clickSpy).toHaveBeenCalled();

    await user.upload(input, pdfFile());

    await waitFor(() => expect(postCalls()).toHaveLength(1));
    const [path, init] = postCalls()[0];
    expect(path).toBe('/nutrition/menus');
    expect((init as RequestInit).body).toBeInstanceOf(FormData);
    // Stays on the list: no intermediate upload view.
    expect(screen.getByText('Tus menús subidos')).toBeInTheDocument();
    expect(input.value).toBe('');
  });

  it('shows a skeleton card and disables the CTA while pending, then shows the new menu', async () => {
    const user = userEvent.setup();
    const { resolveUpload } = mockApiWithUpload(MENUS_FIXTURE);
    renderWithProviders(<NutritionPage />);
    await screen.findByText('Plan Semana 1');

    await user.upload(screen.getByLabelText('Archivo PDF del menú'), pdfFile());

    expect(await screen.findByRole('status', { name: 'Leyendo tu PDF' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Leyendo PDF/i })).toBeDisabled();
    expect(screen.getByText('Plan Semana 1')).toBeInTheDocument();

    resolveUpload();

    expect(await screen.findByText('Plan Semana 3')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByRole('status', { name: 'Leyendo tu PDF' })).not.toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /Subir menú/i })).toBeEnabled();
  });

  it('replaces the empty state with the skeleton while pending', async () => {
    const user = userEvent.setup();
    mockApiWithUpload([]);
    renderWithProviders(<NutritionPage />);
    await screen.findByText('Sin menús todavía');

    await user.upload(screen.getByLabelText('Archivo PDF del menú'), pdfFile());

    expect(await screen.findByRole('status', { name: 'Leyendo tu PDF' })).toBeInTheDocument();
    expect(screen.queryByText('Sin menús todavía')).not.toBeInTheDocument();
  });

  it('shows an inline error when the upload fails and lets the user retry', async () => {
    const user = userEvent.setup();
    const { rejectUpload } = mockApiWithUpload(MENUS_FIXTURE);
    renderWithProviders(<NutritionPage />);
    await screen.findByText('Plan Semana 1');

    await user.upload(screen.getByLabelText('Archivo PDF del menú'), pdfFile());
    await screen.findByRole('status', { name: 'Leyendo tu PDF' });

    rejectUpload();

    expect(
      await screen.findByText('No se pudo leer el PDF. Inténtalo de nuevo.'),
    ).toBeInTheDocument();
    expect(screen.queryByRole('status', { name: 'Leyendo tu PDF' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Subir menú/i })).toBeEnabled();
  });
});

describe('NutritionPage — menu view', () => {
  it('shows menu detail (WeeklyMenuView) when a menu card is clicked', async () => {
    const user = userEvent.setup();
    mockApi();
    renderWithProviders(<NutritionPage />);

    await waitFor(() => screen.getByText('Plan Semana 1'));

    await user.click(screen.getByText('Plan Semana 1'));

    await waitFor(() => {
      // WeeklyMenuView shows day chips
      expect(screen.getByText('Lun')).toBeInTheDocument();
    });
  });
});

describe('NutritionPage — delete menu', () => {
  function mockApiWithDelete() {
    let menus = [...MENUS_FIXTURE];
    mockApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (init?.method === 'DELETE') {
        const id = path.split('/').pop();
        menus = menus.filter((m) => m.id !== id);
        return Promise.resolve(undefined);
      }
      if (path === '/nutrition/menus') return Promise.resolve(menus);
      if (path.startsWith('/nutrition/menus/')) return Promise.resolve(MENU_DETAIL);
      return Promise.resolve(undefined);
    });
  }

  const deleteCalls = () =>
    mockApiFetch.mock.calls.filter(([, init]) => (init as RequestInit | undefined)?.method === 'DELETE');

  it('deletes the shown menu after confirmation and returns to the refreshed list', async () => {
    const user = userEvent.setup();
    mockApiWithDelete();
    renderWithProviders(<NutritionPage />);

    await user.click(await screen.findByText('Plan Semana 1'));
    await screen.findByText('Lun');

    await user.click(screen.getByRole('button', { name: 'Eliminar menú Plan Semana 1' }));
    expect(screen.getByText('¿Seguro?')).toBeInTheDocument();
    expect(deleteCalls()).toHaveLength(0);

    await user.click(screen.getByRole('button', { name: 'Sí' }));

    await waitFor(() => {
      expect(screen.getByText('Tus menús subidos')).toBeInTheDocument();
    });
    expect(mockApiFetch).toHaveBeenCalledWith('/nutrition/menus/m1', { method: 'DELETE' });
    await waitFor(() => {
      expect(screen.queryByText('Plan Semana 1')).not.toBeInTheDocument();
    });
    expect(screen.getByText('Plan Semana 2')).toBeInTheDocument();
  });

  it('shows the empty state after deleting the last menu from the list', async () => {
    const user = userEvent.setup();
    let menus = [MENUS_FIXTURE[0]];
    mockApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (init?.method === 'DELETE') {
        menus = [];
        return Promise.resolve(undefined);
      }
      if (path === '/nutrition/menus') return Promise.resolve(menus);
      return Promise.resolve(MENU_DETAIL);
    });
    renderWithProviders(<NutritionPage />);

    await user.click(await screen.findByRole('button', { name: 'Eliminar menú Plan Semana 1' }));
    // Confirm step must not open the menu detail (click does not bubble to the card).
    expect(screen.getByText('Tus menús subidos')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Sí' }));

    expect(await screen.findByText('Sin menús todavía')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Subir menú/i })).toBeInTheDocument();
  });

  it('does not send a request when the confirmation is cancelled', async () => {
    const user = userEvent.setup();
    mockApiWithDelete();
    renderWithProviders(<NutritionPage />);

    await user.click(await screen.findByText('Plan Semana 1'));
    await screen.findByText('Lun');

    await user.click(screen.getByRole('button', { name: 'Eliminar menú Plan Semana 1' }));
    await user.click(screen.getByRole('button', { name: 'No' }));

    expect(deleteCalls()).toHaveLength(0);
    expect(screen.queryByText('¿Seguro?')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Eliminar menú Plan Semana 1' })).toBeInTheDocument();
    expect(screen.getByText('Lun')).toBeInTheDocument();
  });
});
