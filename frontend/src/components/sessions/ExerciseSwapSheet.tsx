import { useEffect, useRef, useState } from 'react';
import { ImageOff, X } from 'lucide-react';
import { getExerciseGuide } from '../../data/exerciseGuides';
import type { ExerciseResponse } from '../../types/api';

interface ExerciseSwapSheetProps {
  // Exercise currently shown in the slot (planned or substitute).
  current: ExerciseResponse | undefined;
  currentName: string;
  catalog: ExerciseResponse[];
  isPending: boolean;
  errorMessage: string | null;
  onSelect: (exerciseId: string) => void;
  onClose: () => void;
}

/** Pick the catalog exercise to do instead of the current one, this session only. */
export function ExerciseSwapSheet({
  current,
  currentName,
  catalog,
  isPending,
  errorMessage,
  onSelect,
  onClose,
}: ExerciseSwapSheetProps) {
  // Same muscle group first: the usual swap is a similar exercise.
  const [muscleGroup, setMuscleGroup] = useState<string | null>(current?.muscle_group ?? null);
  const initialChipRef = useRef<HTMLButtonElement>(null);

  // The preselected group can sit beyond the visible chips on a phone.
  useEffect(() => {
    initialChipRef.current?.scrollIntoView?.({ block: 'nearest', inline: 'center' });
  }, []);

  const muscleGroups = [...new Set(catalog.map((e) => e.muscle_group))].sort();
  const displayed = catalog
    .filter((e) => e.id !== current?.id && (muscleGroup === null || e.muscle_group === muscleGroup))
    .sort((a, b) => {
      const mg = a.muscle_group.localeCompare(b.muscle_group);
      return mg !== 0 ? mg : a.name.localeCompare(b.name);
    });

  const thumbnailStyle = {
    width: '56px',
    height: '56px',
    borderRadius: '10px',
    flexShrink: 0,
  } as const;

  const chip = (selected: boolean) => ({
    height: '28px',
    padding: '0 12px',
    cursor: 'pointer',
    backgroundColor: selected ? 'var(--neon-green)' : 'var(--bg-elevated)',
    color: selected ? 'var(--bg)' : 'var(--text-muted)',
    border: selected ? '1px solid var(--neon-green)' : '1px solid var(--border)',
  });

  return (
    <div
      className="fixed inset-0 z-50 flex items-end md:items-center justify-center bg-black/60"
      role="dialog"
      aria-modal="true"
      aria-label={`Cambiar ${currentName}`}
      onClick={onClose}
    >
      <div
        className="w-full md:max-w-md flex flex-col"
        style={{
          maxHeight: '80vh',
          background: '#111511',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: '20px 20px 0 0',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-4 pt-4 pb-2 shrink-0">
          <div className="min-w-0">
            <h2 className="text-base font-bold text-text truncate" style={{ margin: 0 }}>
              Cambiar {currentName}
            </h2>
            <p className="text-xs text-muted">Solo para esta sesión</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="bg-transparent border-none cursor-pointer text-muted p-1"
          >
            <X size={20} />
          </button>
        </div>

        <div
          className="flex gap-2 overflow-x-auto overflow-y-hidden px-4 py-2 border-b border-border shrink-0"
          role="group"
          aria-label="Filtrar por grupo muscular"
        >
          <button
            type="button"
            onClick={() => setMuscleGroup(null)}
            className="text-xs font-semibold rounded-btn shrink-0"
            style={chip(muscleGroup === null)}
          >
            Todos
          </button>
          {muscleGroups.map((mg) => (
            <button
              key={mg}
              ref={mg === current?.muscle_group ? initialChipRef : undefined}
              type="button"
              onClick={() => setMuscleGroup(mg)}
              className="text-xs font-semibold rounded-btn shrink-0"
              style={chip(muscleGroup === mg)}
            >
              {mg}
            </button>
          ))}
        </div>

        {errorMessage && <p className="text-sm text-danger px-4 pt-3 shrink-0">{errorMessage}</p>}

        <ul className="overflow-y-auto flex-1 min-h-0" style={{ margin: 0, padding: 0, listStyle: 'none' }}>
          {displayed.length === 0 ? (
            <li className="text-sm italic text-muted px-4 py-6">No hay ejercicios disponibles.</li>
          ) : (
            displayed.map((exercise) => {
              const photo = getExerciseGuide(exercise.id)?.photos[0];
              return (
                <li key={exercise.id} className="border-b border-border">
                  <button
                    type="button"
                    disabled={isPending}
                    onClick={() => onSelect(exercise.id)}
                    className="w-full text-left px-4 py-2 bg-transparent border-none cursor-pointer flex items-center gap-3"
                  >
                    {photo ? (
                      <img
                        src={photo}
                        alt=""
                        loading="lazy"
                        style={{ ...thumbnailStyle, objectFit: 'cover', background: '#EAF0EA' }}
                      />
                    ) : (
                      <span
                        aria-hidden="true"
                        className="flex items-center justify-center text-muted"
                        style={{
                          ...thumbnailStyle,
                          background: 'rgba(255,255,255,0.05)',
                          border: '1px dashed rgba(255,255,255,0.15)',
                        }}
                      >
                        <ImageOff size={20} />
                      </span>
                    )}
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-medium text-text truncate">{exercise.name}</span>
                      <span className="block text-xs text-muted">
                        {exercise.muscle_group}
                        {!photo && (
                          <>
                            {' · '}
                            <span>Sin foto todavía</span>
                          </>
                        )}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })
          )}
        </ul>
      </div>
    </div>
  );
}
