import { useState } from 'react';
import type { DayMeal, MealOption } from '../../types/api';

interface MealCardProps {
  label: string;
  meal: DayMeal | null;
  options?: MealOption[];
  isFree?: boolean;
}

const CARD_STYLE: React.CSSProperties = {
  background: '#14160F',
  border: '1px solid #22251E',
  borderRadius: '16px',
  padding: '16px',
  marginBottom: '12px',
};

const LABEL_STYLE: React.CSSProperties = {
  fontSize: '11px',
  fontWeight: 700,
  color: '#2BE581',
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  marginBottom: '6px',
};

const MEAL_NAME_STYLE: React.CSSProperties = {
  fontSize: '16px',
  fontWeight: 600,
  color: 'var(--text)',
  marginBottom: '8px',
};

const INGREDIENT_STYLE: React.CSSProperties = {
  fontSize: '13px',
  color: '#8B928A',
  margin: '2px 0',
};

const LIBRE_BADGE_STYLE: React.CSSProperties = {
  display: 'inline-block',
  background: '#1D2019',
  color: '#8B928A',
  borderRadius: '8px',
  padding: '4px 10px',
  fontSize: '13px',
  fontWeight: 600,
};

const PILL_BASE: React.CSSProperties = {
  display: 'inline-block',
  padding: '5px 12px',
  borderRadius: '20px',
  fontSize: '13px',
  fontWeight: 600,
  cursor: 'pointer',
  border: 'none',
  marginRight: '8px',
  marginBottom: '8px',
};

export function MealCard({ label, meal, options, isFree }: MealCardProps) {
  const [selectedOptionIndex, setSelectedOptionIndex] = useState(0);

  const renderIngredients = (ingredients: string[]) => (
    <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
      {ingredients.map((ingredient) => (
        <li key={ingredient} style={INGREDIENT_STYLE}>
          {ingredient}
        </li>
      ))}
    </ul>
  );

  // Options mode (shared meals: desayuno, almuerzo, merienda)
  if (options && options.length > 0) {
    const selected = options[selectedOptionIndex];
    return (
      <div style={CARD_STYLE}>
        <div style={LABEL_STYLE}>{label}</div>
        <div style={{ marginBottom: '10px' }}>
          {options.map((opt, i) => (
            <button
              key={opt.name}
              type="button"
              onClick={() => setSelectedOptionIndex(i)}
              style={{
                ...PILL_BASE,
                background: i === selectedOptionIndex ? '#2BE581' : '#1D2019',
                color: i === selectedOptionIndex ? '#090B09' : '#8B928A',
              }}
            >
              {opt.name}
            </button>
          ))}
        </div>
        {renderIngredients(selected.ingredients)}
      </div>
    );
  }

  // Free day meal
  if (isFree || meal?.is_free) {
    return (
      <div style={CARD_STYLE}>
        <div style={LABEL_STYLE}>{label}</div>
        <span style={LIBRE_BADGE_STYLE}>Libre</span>
      </div>
    );
  }

  // Fixed meal
  if (meal) {
    return (
      <div style={CARD_STYLE}>
        <div style={LABEL_STYLE}>{label}</div>
        <div style={MEAL_NAME_STYLE}>{meal.name}</div>
        {renderIngredients(meal.ingredients)}
      </div>
    );
  }

  return null;
}
