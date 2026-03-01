import type { Meal } from '../../types';

interface MealPlanViewProps {
  meals: Meal[];
  onMealClick: (meal: Meal) => void;
}

export const MealPlanView = ({ meals, onMealClick }: MealPlanViewProps) => {
  // Group meals by date
  const mealsByDate = meals.reduce((acc, meal) => {
    if (!acc[meal.date]) {
      acc[meal.date] = [];
    }
    acc[meal.date].push(meal);
    return acc;
  }, {} as Record<string, Meal[]>);

  const dates = Object.keys(mealsByDate).sort();

  if (meals.length === 0) {
    return (
      <div className="ds-card flex items-center justify-center p-12 text-center">
        <p className="ds-body-text text-lg">No meals scheduled. Your meal plan will appear here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="ds-heading-lg mb-4">Weekly Meal Plan</h2>
      
      <div className="grid gap-4">
        {dates.map((date) => {
          const dateMeals = mealsByDate[date];
          const dateObj = new Date(date);
          const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' });
          const dateStr = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

          return (
            <div key={date} className="ds-card" style={{ padding: '1.5rem' }}>
              <div className="mb-4">
                <h3 className="ds-heading-sm m-0">{dayName}</h3>
                <p className="ds-body-text text-sm">{dateStr}</p>
              </div>

              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {dateMeals.map((meal) => (
                  <button
                    key={meal.id}
                    onClick={() => onMealClick(meal)}
                    className="text-left p-4 rounded-xl transition-all duration-300"
                    style={{
                      background: 'var(--color-bg-elevated)',
                      border: '1px solid var(--color-border)',
                      cursor: 'pointer'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'var(--color-border-hover)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--color-border)';
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-bold tracking-wider uppercase ds-gradient-text">
                        {meal.mealType.replace('_', ' ')}
                      </span>
                      <span className="text-xs font-medium" style={{ color: 'var(--color-text-faint)' }}>
                        {meal.scheduledTime}
                      </span>
                    </div>
                    <h4 className="font-semibold mb-2" style={{ color: 'var(--color-text-primary)', fontSize: '1.05rem', lineHeight: '1.3' }}>
                      {meal.dish.name}
                    </h4>
                    <div className="flex items-center gap-2 text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>
                      <span>{meal.dish.macros.calories} kcal</span>
                      <span style={{ color: 'var(--color-border)' }}>|</span>
                      <span>P: {meal.dish.macros.protein}g</span>
                      <span style={{ color: 'var(--color-border)' }}>|</span>
                      <span>C: {meal.dish.macros.carbs}g</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
