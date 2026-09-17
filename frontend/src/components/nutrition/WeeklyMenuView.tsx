import { useState } from 'react';
import type { ParsedMenu } from '../../types/api';
import { MealCard } from './MealCard';

interface WeeklyMenuViewProps {
  menu: ParsedMenu;
}

const DAY_CHIPS = [
  { short: 'Lun', index: 0 },
  { short: 'Mar', index: 1 },
  { short: 'Mié', index: 2 },
  { short: 'Jue', index: 3 },
  { short: 'Vie', index: 4 },
  { short: 'Sáb', index: 5 },
  { short: 'Dom', index: 6 },
];

export function WeeklyMenuView({ menu }: WeeklyMenuViewProps) {
  const [selectedDay, setSelectedDay] = useState(0);

  const day = menu.days[selectedDay];

  return (
    <div>
      {/* Day chips row */}
      <div
        style={{
          display: 'flex',
          overflowX: 'auto',
          gap: '8px',
          paddingBottom: '12px',
          marginBottom: '16px',
        }}
      >
        {DAY_CHIPS.map(({ short, index }) => {
          const active = index === selectedDay;
          return (
            <button
              key={short}
              type="button"
              onClick={() => setSelectedDay(index)}
              style={{
                flexShrink: 0,
                padding: '8px 16px',
                borderRadius: '20px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: 700,
                background: active ? '#2BE581' : '#1D2019',
                color: active ? '#090B09' : '#8B928A',
              }}
            >
              {short}
            </button>
          );
        })}
      </div>

      {/* Meal cards */}
      {day && (
        <>
          <MealCard
            label="Desayuno"
            meal={null}
            options={menu.shared.desayuno}
          />
          <MealCard
            label="Almuerzo"
            meal={null}
            options={menu.shared.almuerzo_options}
          />
          <MealCard
            key={`comida-${selectedDay}`}
            label="Comida"
            meal={day.comida}
            isFree={day.comida.is_free}
          />
          <MealCard
            label="Merienda"
            meal={null}
            options={menu.shared.merienda}
          />
          <MealCard
            key={`cena-${selectedDay}`}
            label="Cena"
            meal={day.cena}
            isFree={day.cena.is_free}
          />
        </>
      )}
    </div>
  );
}
