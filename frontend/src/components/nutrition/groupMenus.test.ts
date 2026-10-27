import { groupMenus } from './groupMenus';
import type { DietPlanSummary } from '../../types/api';

function summary(over: Partial<DietPlanSummary> & { id: string }): DietPlanSummary {
  return {
    user_id: 'u1',
    title: 'Plan',
    calories: null,
    uploaded_at: '2026-10-01T00:00:00Z',
    group_id: null,
    person: null,
    ...over,
  };
}

describe('groupMenus', () => {
  it('merges variants sharing a group_id into one group, highest calories first', () => {
    const groups = groupMenus([
      summary({ id: 'b1', title: 'Quinoa', calories: 1500, group_id: 'g1', person: 'Belén' }),
      summary({ id: 'f1', title: 'Quinoa', calories: 2100, group_id: 'g1', person: 'Fede' }),
    ]);

    expect(groups).toHaveLength(1);
    expect(groups[0].title).toBe('Quinoa');
    expect(groups[0].variants.map((v) => v.person)).toEqual(['Fede', 'Belén']);
    expect(groups[0].variants.map((v) => v.id)).toEqual(['f1', 'b1']);
  });

  it('keeps plans without group_id as single-variant groups', () => {
    const groups = groupMenus([summary({ id: 'm1' }), summary({ id: 'm2' })]);

    expect(groups.map((g) => g.variants.map((v) => v.id))).toEqual([['m1'], ['m2']]);
  });

  it('preserves the list order by first appearance of each group', () => {
    const groups = groupMenus([
      summary({ id: 'a1', title: 'A', group_id: 'gA', person: 'Fede' }),
      summary({ id: 'solo', title: 'Solo' }),
      summary({ id: 'a2', title: 'A', group_id: 'gA', person: 'Belén' }),
    ]);

    expect(groups.map((g) => g.title)).toEqual(['A', 'Solo']);
  });

  it('puts variants without calories last', () => {
    const groups = groupMenus([
      summary({ id: 'x', calories: null, group_id: 'g', person: 'X' }),
      summary({ id: 'y', calories: 1500, group_id: 'g', person: 'Y' }),
    ]);

    expect(groups[0].variants.map((v) => v.id)).toEqual(['y', 'x']);
  });
});
