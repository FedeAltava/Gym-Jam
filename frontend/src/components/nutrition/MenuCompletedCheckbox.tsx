import { useSetMenuCompleted } from '../../hooks/useNutrition';

interface MenuCompletedCheckboxProps {
  /** Any variant of the menu: the backend ticks the whole group. */
  menuId: string;
  menuTitle: string;
  completed: boolean;
}

export function MenuCompletedCheckbox({ menuId, menuTitle, completed }: MenuCompletedCheckboxProps) {
  const mutation = useSetMenuCompleted();

  return (
    // Stop clicks from bubbling to the clickable menu card.
    <div onClick={(e) => e.stopPropagation()} style={{ marginTop: '10px' }}>
      <label
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          cursor: 'pointer',
          fontSize: '13px',
          fontWeight: 600,
          color: completed ? '#2BE581' : '#8B928A',
        }}
      >
        <input
          type="checkbox"
          checked={completed}
          onChange={(e) => mutation.mutate({ id: menuId, completed: e.target.checked })}
          aria-label={`Completado: ${menuTitle}`}
          style={{ width: '18px', height: '18px', accentColor: '#2BE581', cursor: 'pointer', margin: 0 }}
        />
        Completado
      </label>
      {mutation.isError && (
        <p className="mt-1 text-xs text-danger">No se pudo guardar. Inténtalo de nuevo.</p>
      )}
    </div>
  );
}
