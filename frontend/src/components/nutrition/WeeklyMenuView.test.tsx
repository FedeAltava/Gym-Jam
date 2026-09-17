import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/test-utils';
import { WeeklyMenuView } from './WeeklyMenuView';
import type { ParsedMenu } from '../../types/api';

const PARSED_MENU: ParsedMenu = {
  title: 'Plan Semana Test',
  calories: 2000,
  shared: {
    desayuno: [
      { name: 'Opción A', ingredients: ['Leche', 'Avena'] },
      { name: 'Opción B', ingredients: ['Yogur', 'Fruta'] },
    ],
    almuerzo_options: [
      { name: 'Ensalada', ingredients: ['Lechuga', 'Tomate'] },
    ],
    merienda: [
      { name: 'Snack', ingredients: ['Manzana'] },
    ],
  },
  days: [
    {
      day: 'Lunes',
      comida: { name: 'Pollo', ingredients: ['Pollo 150g', 'Arroz'], is_free: false },
      cena: { name: 'Libre', ingredients: [], is_free: true },
    },
    {
      day: 'Martes',
      comida: { name: 'Ternera', ingredients: ['Ternera 200g', 'Patatas'], is_free: false },
      cena: { name: 'Pescado', ingredients: ['Merluza', 'Verduras'], is_free: false },
    },
    {
      day: 'Miércoles',
      comida: { name: 'Pasta', ingredients: ['Pasta 100g'], is_free: false },
      cena: { name: 'Libre', ingredients: [], is_free: true },
    },
    {
      day: 'Jueves',
      comida: { name: 'Arroz', ingredients: ['Arroz 80g', 'Pollo'], is_free: false },
      cena: { name: 'Tortilla', ingredients: ['Huevos', 'Patata'], is_free: false },
    },
    {
      day: 'Viernes',
      comida: { name: 'Lentejas', ingredients: ['Lentejas 100g'], is_free: false },
      cena: { name: 'Libre', ingredients: [], is_free: true },
    },
    {
      day: 'Sábado',
      comida: { name: 'Libre', ingredients: [], is_free: true },
      cena: { name: 'Libre', ingredients: [], is_free: true },
    },
    {
      day: 'Domingo',
      comida: { name: 'Paella', ingredients: ['Arroz', 'Marisco'], is_free: false },
      cena: { name: 'Libre', ingredients: [], is_free: true },
    },
  ],
};

describe('WeeklyMenuView', () => {
  it('renders 7 day chips (Lun through Dom)', () => {
    renderWithProviders(<WeeklyMenuView menu={PARSED_MENU} />);

    expect(screen.getByText('Lun')).toBeInTheDocument();
    expect(screen.getByText('Mar')).toBeInTheDocument();
    expect(screen.getByText('Mié')).toBeInTheDocument();
    expect(screen.getByText('Jue')).toBeInTheDocument();
    expect(screen.getByText('Vie')).toBeInTheDocument();
    expect(screen.getByText('Sáb')).toBeInTheDocument();
    expect(screen.getByText('Dom')).toBeInTheDocument();
  });

  it('shows Lunes data by default (first day selected)', () => {
    renderWithProviders(<WeeklyMenuView menu={PARSED_MENU} />);

    // Comida for Lunes
    expect(screen.getByText('Pollo')).toBeInTheDocument();
    expect(screen.getByText('Pollo 150g')).toBeInTheDocument();
    // Cena for Lunes is free
    expect(screen.getByText('Libre')).toBeInTheDocument();
    // Shared: desayuno options shown
    expect(screen.getByText('Opción A')).toBeInTheDocument();
  });

  it('switches content when a different day chip is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<WeeklyMenuView menu={PARSED_MENU} />);

    // Default: Lunes — shows Pollo
    expect(screen.getByText('Pollo')).toBeInTheDocument();

    // Click Martes
    await user.click(screen.getByText('Mar'));

    // Now shows Martes comida: Ternera
    expect(screen.getByText('Ternera')).toBeInTheDocument();
    expect(screen.getByText('Ternera 200g')).toBeInTheDocument();
    // And Martes cena: Pescado
    expect(screen.getByText('Pescado')).toBeInTheDocument();
    // Pollo no longer shown
    expect(screen.queryByText('Pollo')).not.toBeInTheDocument();
  });

  it('renders meal section labels for all 5 meals', () => {
    renderWithProviders(<WeeklyMenuView menu={PARSED_MENU} />);

    expect(screen.getByText('Desayuno')).toBeInTheDocument();
    expect(screen.getByText('Almuerzo')).toBeInTheDocument();
    expect(screen.getByText('Comida')).toBeInTheDocument();
    expect(screen.getByText('Merienda')).toBeInTheDocument();
    expect(screen.getByText('Cena')).toBeInTheDocument();
  });
});
