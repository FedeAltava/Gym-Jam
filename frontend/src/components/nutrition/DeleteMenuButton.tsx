import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { useDeleteDietPlan } from '../../hooks/useNutrition';

interface DeleteMenuButtonProps {
  menuId: string;
  menuTitle: string;
  onDeleted?: () => void;
}

/**
 * Inline two-step delete (Eliminar → ¿Seguro? Sí / No), mirroring the
 * workout delete control in WorkoutDetailPage.
 */
export function DeleteMenuButton({ menuId, menuTitle, onDeleted }: DeleteMenuButtonProps) {
  const [confirming, setConfirming] = useState(false);
  const deleteMutation = useDeleteDietPlan();

  const handleConfirm = () => {
    deleteMutation.mutate(menuId, {
      onSuccess: () => {
        setConfirming(false);
        onDeleted?.();
      },
    });
  };

  return (
    // Stop clicks from bubbling to a clickable parent (e.g. a menu card).
    <div onClick={(e) => e.stopPropagation()}>
      {!confirming ? (
        <button
          type="button"
          onClick={() => setConfirming(true)}
          className="flex items-center gap-1.5 text-sm font-semibold rounded-btn border border-danger text-danger transition-colors hover:bg-danger hover:text-bg"
          style={{ height: '36px', padding: '0 12px', backgroundColor: 'transparent', cursor: 'pointer' }}
          aria-label={`Eliminar menú ${menuTitle}`}
        >
          <Trash2 size={15} />
          Eliminar
        </button>
      ) : (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted font-semibold">¿Seguro?</span>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={deleteMutation.isPending}
            className="text-sm font-semibold rounded-btn bg-danger text-bg disabled:opacity-60"
            style={{ height: '36px', padding: '0 12px', border: 'none', cursor: 'pointer' }}
          >
            {deleteMutation.isPending ? '…' : 'Sí'}
          </button>
          <button
            type="button"
            onClick={() => setConfirming(false)}
            className="text-sm font-semibold rounded-btn border border-border text-muted"
            style={{ height: '36px', padding: '0 12px', backgroundColor: 'transparent', cursor: 'pointer' }}
          >
            No
          </button>
        </div>
      )}
      {deleteMutation.isError && (
        <p className="mt-2 text-xs text-danger">No se pudo eliminar el menú. Inténtalo de nuevo.</p>
      )}
    </div>
  );
}
