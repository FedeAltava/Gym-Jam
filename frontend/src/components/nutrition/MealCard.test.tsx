import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/test-utils';
import { MealCard } from './MealCard';
import type { DayMeal, MealOption } from '../../types/api';

const FIXED_MEAL: DayMeal = {
  name: 'Pollo con arroz',
  ingredients: ['Pollo 150g', 'Arroz 80g', 'Aceite de oliva'],
  is_free: false,
};

const FREE_MEAL: DayMeal = {
  name: 'Libre',
  ingredients: [],
  is_free: true,
};

const OPTIONS: MealOption[] = [
  { name: 'Opción A', ingredients: ['Leche', 'Avena'] },
  { name: 'Opción B', ingredients: ['Yogur', 'Fruta'] },
];

describe('MealCard — fixed meal', () => {
  it('renders the meal name and all ingredients', () => {
    renderWithProviders(<MealCard label="Comida" meal={FIXED_MEAL} />);

    expect(screen.getByText('Comida')).toBeInTheDocument();
    expect(screen.getByText('Pollo con arroz')).toBeInTheDocument();
    expect(screen.getByText('Pollo 150g')).toBeInTheDocument();
    expect(screen.getByText('Arroz 80g')).toBeInTheDocument();
    expect(screen.getByText('Aceite de oliva')).toBeInTheDocument();
  });

  it('does not render a Libre badge for fixed meals', () => {
    renderWithProviders(<MealCard label="Cena" meal={FIXED_MEAL} />);
    expect(screen.queryByText('Libre')).not.toBeInTheDocument();
  });
});

describe('MealCard — free meal (is_free)', () => {
  it('renders the Libre badge when meal is_free', () => {
    renderWithProviders(<MealCard label="Cena" meal={FREE_MEAL} isFree />);

    expect(screen.getByText('Cena')).toBeInTheDocument();
    expect(screen.getByText('Libre')).toBeInTheDocument();
  });

  it('does not show ingredient list when is_free', () => {
    renderWithProviders(<MealCard label="Cena" meal={FREE_MEAL} isFree />);
    // No ingredients for free meal
    expect(screen.queryByRole('list')).not.toBeInTheDocument();
  });
});

describe('MealCard — options (shared meals)', () => {
  it('renders option pills and selects the first by default', () => {
    renderWithProviders(<MealCard label="Desayuno" meal={null} options={OPTIONS} />);

    expect(screen.getByText('Opción A')).toBeInTheDocument();
    expect(screen.getByText('Opción B')).toBeInTheDocument();
    // First option selected: show its ingredients
    expect(screen.getByText('Leche')).toBeInTheDocument();
    expect(screen.getByText('Avena')).toBeInTheDocument();
  });

  it('switches ingredient list when another option pill is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MealCard label="Desayuno" meal={null} options={OPTIONS} />);

    // Initially shows Opción A ingredients
    expect(screen.getByText('Leche')).toBeInTheDocument();

    // Click Opción B pill
    await user.click(screen.getByText('Opción B'));

    // Now shows Opción B ingredients
    expect(screen.getByText('Yogur')).toBeInTheDocument();
    expect(screen.getByText('Fruta')).toBeInTheDocument();
    // Opción A ingredients gone
    expect(screen.queryByText('Leche')).not.toBeInTheDocument();
  });
});
