import { keepPreviousData, useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { DietPlan, DietPlanSummary } from '../types/api';

export function useNutritionMenus() {
  return useQuery({
    queryKey: ['nutrition', 'menus'],
    queryFn: () => apiFetch<DietPlanSummary[]>('/nutrition/menus'),
  });
}

/**
 * keepPrevious keeps showing the last loaded plan while another id loads,
 * e.g. when switching between the variants of one menu.
 */
export function useNutritionMenu(id: string, { keepPrevious = false } = {}) {
  return useQuery({
    queryKey: ['nutrition', 'menus', id],
    queryFn: () => apiFetch<DietPlan>(`/nutrition/menus/${id}`),
    enabled: !!id,
    placeholderData: keepPrevious ? keepPreviousData : undefined,
  });
}

export function useUploadNutritionMenu() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) =>
      apiFetch<DietPlan>('/nutrition/menus', {
        method: 'POST',
        body: formData,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['nutrition', 'menus'] }),
  });
}

export function useDeleteDietPlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/nutrition/menus/${id}`, { method: 'DELETE' }),
    onSuccess: (_data, id) => {
      // Drop the deleted plan's detail cache and refresh only the list, so no
      // refetch is ever issued for a plan that no longer exists.
      qc.removeQueries({ queryKey: ['nutrition', 'menus', id], exact: true });
      return qc.invalidateQueries({ queryKey: ['nutrition', 'menus'], exact: true });
    },
  });
}

/**
 * Tick or untick a menu. The backend applies it to every variant of the
 * plan's group, so the list cache mirrors that optimistically and rolls back
 * if the request fails.
 */
export function useSetMenuCompleted() {
  const qc = useQueryClient();
  const listKey = ['nutrition', 'menus'];
  return useMutation({
    mutationFn: ({ id, completed }: { id: string; completed: boolean }) =>
      apiFetch<void>(`/nutrition/menus/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ completed }),
      }),
    onMutate: async ({ id, completed }) => {
      await qc.cancelQueries({ queryKey: listKey, exact: true });
      const previous = qc.getQueryData<DietPlanSummary[]>(listKey);
      if (previous) {
        const groupId = previous.find((m) => m.id === id)?.group_id;
        qc.setQueryData<DietPlanSummary[]>(
          listKey,
          previous.map((m) =>
            m.id === id || (groupId && m.group_id === groupId) ? { ...m, completed } : m,
          ),
        );
      }
      return { previous };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.previous) qc.setQueryData(listKey, ctx.previous);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: listKey, exact: true }),
  });
}
