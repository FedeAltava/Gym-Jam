import { useMutation } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';

interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (data: ChangePasswordPayload) =>
      apiFetch<void>('/auth/password', {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
  });
}
