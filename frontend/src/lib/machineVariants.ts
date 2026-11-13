// Machine exercises come in two catalog variants: plate-loaded "(discos)" and
// selectorized "(placas)" (backend migration 023). Their ids differ only in
// the suffix, so each variant's twin is found by swapping it.
const PLATE_LOADED = '-plate-loaded';
const SELECTORIZED = '-selectorized';

export interface MachineTwin {
  id: string;
  label: 'discos' | 'placas';
}

/** The other machine type of the same exercise, or null when it has none. */
export function machineTwin(exerciseId: string): MachineTwin | null {
  if (exerciseId.endsWith(PLATE_LOADED)) {
    return { id: exerciseId.slice(0, -PLATE_LOADED.length) + SELECTORIZED, label: 'placas' };
  }
  if (exerciseId.endsWith(SELECTORIZED)) {
    return { id: exerciseId.slice(0, -SELECTORIZED.length) + PLATE_LOADED, label: 'discos' };
  }
  return null;
}
