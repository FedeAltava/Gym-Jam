import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { BodyWeightEntryResponse } from '../types/api';

const BODY_WEIGHT_KEY = ['body-weight'] as const;

/** The user's weigh-ins, newest day first. */
export function useBodyWeightHistory() {
  return useQuery({
    queryKey: BODY_WEIGHT_KEY,
    queryFn: () => apiFetch<BodyWeightEntryResponse[]>('/users/me/body-weight'),
  });
}

/** Record a day's weight; a day that already has one is replaced. */
export function useRecordBodyWeight() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ measuredOn, weightKg }: { measuredOn: string; weightKg: number }) =>
      apiFetch<BodyWeightEntryResponse>(`/users/me/body-weight/${measuredOn}`, {
        method: 'PUT',
        body: JSON.stringify({ weight_kg: weightKg }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: BODY_WEIGHT_KEY }),
  });
}

export function useDeleteBodyWeight() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (measuredOn: string) =>
      apiFetch<void>(`/users/me/body-weight/${measuredOn}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: BODY_WEIGHT_KEY }),
  });
}
