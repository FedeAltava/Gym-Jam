import type { DietPlanSummary } from '../../types/api';

export interface MenuVariant {
  id: string;
  person: string | null;
  calories: number | null;
}

export interface MenuGroup {
  key: string;
  title: string;
  uploaded_at: string;
  /** The variants of a menu are ticked together, so they share this flag. */
  completed: boolean;
  /** Highest calories first, so the larger portion (Fede) is the default. */
  variants: MenuVariant[];
}

/**
 * Collapse the per-person variants of a menu (same group_id) into one entry.
 * Plans without group_id stay as single-variant groups. Groups keep the order
 * in which they first appear in the list.
 */
export function groupMenus(menus: DietPlanSummary[]): MenuGroup[] {
  const groups = new Map<string, MenuGroup>();
  for (const menu of menus) {
    const key = menu.group_id ?? menu.id;
    const group = groups.get(key) ?? {
      key,
      title: menu.title,
      uploaded_at: menu.uploaded_at,
      completed: true,
      variants: [],
    };
    group.completed &&= menu.completed ?? false;
    group.variants.push({ id: menu.id, person: menu.person ?? null, calories: menu.calories });
    groups.set(key, group);
  }
  for (const group of groups.values()) {
    group.variants.sort((a, b) => (b.calories ?? -1) - (a.calories ?? -1));
  }
  return [...groups.values()];
}
