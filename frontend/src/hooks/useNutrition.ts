import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { DietPlan, DietPlanSummary } from '../types/api';

export function useNutritionMenus() {
  return useQuery({
    queryKey: ['nutrition', 'menus'],
    queryFn: () => apiFetch<DietPlanSummary[]>('/nutrition/menus'),
  });
}

export function useNutritionMenu(id: string) {
  return useQuery({
    queryKey: ['nutrition', 'menus', id],
    queryFn: () => apiFetch<DietPlan>(`/nutrition/menus/${id}`),
    enabled: !!id,
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
