import React from 'react';
import type { UserProfile } from '../../types';
import '../../pages/DashboardPage.css';

interface MealPlanSummaryProps {
  profile: UserProfile;
}

export const MealPlanSummary: React.FC<MealPlanSummaryProps> = ({ profile }) => {
  const { mealPlan } = profile;

  if (!mealPlan || !mealPlan.macros) {
    return (
      <div className="ds-card" style={{ height: '100%' }}>
        <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>🍽️ Meal Plan</h2>
        <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>No meal plan configured yet.</p>
      </div>
    );
  }

  const { protein = 0, carbs = 0, fats = 0 } = mealPlan.macros;
  const totalMacroCals = (protein * 4) + (carbs * 4) + (fats * 9) || 1;

  const macros = [
    { label: 'Protein', grams: protein, pct: Math.round(((protein * 4) / totalMacroCals) * 100), variant: 'protein' },
    { label: 'Carbs', grams: carbs, pct: Math.round(((carbs * 4) / totalMacroCals) * 100), variant: 'carbs' },
    { label: 'Fats', grams: fats, pct: Math.round(((fats * 9) / totalMacroCals) * 100), variant: 'fats' },
  ];

  return (
    <div className="ds-card" style={{ height: '100%' }}>
      <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>🍽️ Meal Plan</h2>

      {/* Calorie Highlight */}
      <div className="flex items-baseline gap-2 mb-5">
        <span className="text-3xl font-extrabold ds-gradient-text">{mealPlan.dailyCalories || 0}</span>
        <span className="text-sm" style={{ color: 'var(--color-text-faint)' }}>kcal / day</span>
        {mealPlan.mealsPerDay && (
          <span className="ml-auto dash-chip">
            {mealPlan.mealsPerDay} meals/day
          </span>
        )}
      </div>

      {/* Macro Bars */}
      <div className="dash-section-title">Macronutrients</div>
      <div className="space-y-3">
        {macros.map((m) => (
          <div key={m.label}>
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>{m.label}</span>
              <span className="text-sm" style={{ color: 'var(--color-text-primary)' }}>
                {m.grams}g
                <span className="ml-1 text-xs" style={{ color: 'var(--color-text-faint)' }}>({m.pct}%)</span>
              </span>
            </div>
            <div className="dash-macro-bar-track">
              <div className={`dash-macro-bar-fill dash-macro-bar-fill--${m.variant}`} style={{ width: `${m.pct}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
