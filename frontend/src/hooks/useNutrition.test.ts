import { renderHook, waitFor, act } from '@testing-library/react';
import { apiFetch } from '../lib/api';
import { createWrapper } from '../test/test-utils';
import {
  useNutritionMenus,
  useNutritionMenu,
  useUploadNutritionMenu,
  useDeleteDietPlan,
} from './useNutrition';
import type { DietPlanSummary, DietPlan } from '../types/api';

vi.mock('../lib/api', async (orig) => ({
  ...(await orig()),
  apiFetch: vi.fn(),
}));

afterEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// useNutritionMenus
// ---------------------------------------------------------------------------

describe('useNutritionMenus', () => {
  it('GETs /nutrition/menus and returns a list', async () => {
    const menus: DietPlanSummary[] = [
      {
        id: 'm1',
        user_id: 'u1',
        title: 'Plan Semana 1',
        calories: 2000,
        uploaded_at: '2026-09-01T00:00:00Z',
      },
    ];
    vi.mocked(apiFetch).mockResolvedValue(menus);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useNutritionMenus(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith('/nutrition/menus');
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0].title).toBe('Plan Semana 1');
  });

  it('returns empty array when no menus exist', async () => {
    vi.mocked(apiFetch).mockResolvedValue([]);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useNutritionMenus(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// useNutritionMenu
// ---------------------------------------------------------------------------

describe('useNutritionMenu', () => {
  it('GETs /nutrition/menus/:id and returns a DietPlan', async () => {
    const plan: DietPlan = {
      id: 'm1',
      user_id: 'u1',
      title: 'Plan Semana 1',
      calories: 2000,
      menu_json: { title: '', calories: null, shared: { desayuno: [], almuerzo_options: [], merienda: [] }, days: [] },
      uploaded_at: '2026-09-01T00:00:00Z',
    };
    vi.mocked(apiFetch).mockResolvedValue(plan);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useNutritionMenu('m1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith('/nutrition/menus/m1');
    expect(result.current.data?.title).toBe('Plan Semana 1');
  });

  it('is disabled when id is empty string', async () => {
    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useNutritionMenu(''), { wrapper });

    // query should stay in pending/idle state (not fetched)
    expect(result.current.isPending).toBe(true);
    expect(vi.mocked(apiFetch)).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// useUploadNutritionMenu
// ---------------------------------------------------------------------------

describe('useUploadNutritionMenu', () => {
  it('POSTs FormData to /nutrition/menus and returns the created plan', async () => {
    const created: DietPlan = {
      id: 'new1',
      user_id: 'u1',
      title: 'Nuevo Plan',
      calories: null,
      menu_json: { title: '', calories: null, shared: { desayuno: [], almuerzo_options: [], merienda: [] }, days: [] },
      uploaded_at: '2026-09-08T00:00:00Z',
    };
    vi.mocked(apiFetch).mockResolvedValue(created);

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useUploadNutritionMenu(), { wrapper });

    const fd = new FormData();
    fd.append('file', new Blob(['pdf'], { type: 'application/pdf' }), 'plan.pdf');

    await act(async () => {
      result.current.mutate(fd);
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith('/nutrition/menus', {
      method: 'POST',
      body: fd,
    });
    expect(result.current.data?.id).toBe('new1');
  });
});

// ---------------------------------------------------------------------------
// useDeleteDietPlan
// ---------------------------------------------------------------------------

describe('useDeleteDietPlan', () => {
  it('DELETEs /nutrition/menus/:id, removes the detail cache and invalidates the list', async () => {
    vi.mocked(apiFetch).mockResolvedValue(undefined);

    const { wrapper, queryClient } = createWrapper();
    queryClient.setQueryData(['nutrition', 'menus'], [{ id: 'm1' }, { id: 'm2' }]);
    queryClient.setQueryData(['nutrition', 'menus', 'm1'], { id: 'm1' });
    queryClient.setQueryData(['nutrition', 'menus', 'm2'], { id: 'm2' });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useDeleteDietPlan(), { wrapper });

    await act(async () => {
      result.current.mutate('m1');
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith('/nutrition/menus/m1', { method: 'DELETE' });
    expect(queryClient.getQueryData(['nutrition', 'menus', 'm1'])).toBeUndefined();
    expect(queryClient.getQueryData(['nutrition', 'menus', 'm2'])).toEqual({ id: 'm2' });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['nutrition', 'menus'], exact: true });
  });

  it('keeps caches untouched when the request fails', async () => {
    vi.mocked(apiFetch).mockRejectedValue(new Error('Not found'));

    const { wrapper, queryClient } = createWrapper();
    queryClient.setQueryData(['nutrition', 'menus', 'm1'], { id: 'm1' });

    const { result } = renderHook(() => useDeleteDietPlan(), { wrapper });

    await act(async () => {
      result.current.mutate('m1');
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(queryClient.getQueryData(['nutrition', 'menus', 'm1'])).toEqual({ id: 'm1' });
  });
});
