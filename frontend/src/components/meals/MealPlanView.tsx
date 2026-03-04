import type { Meal } from '../../types';

const DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

interface MealPlanViewProps {
  meals: Meal[];
  onMealClick: (meal: Meal) => void;
}

export const MealPlanView = ({ meals, onMealClick }: MealPlanViewProps) => {
  // Group meals by day name
  const mealsByDay = meals.reduce((acc, meal) => {
    if (!acc[meal.dayName]) {
      acc[meal.dayName] = [];
    }
    acc[meal.dayName].push(meal);
    return acc;
  }, {} as Record<string, Meal[]>);

  // Sort days in week order
  const days = Object.keys(mealsByDay).sort(
    (a, b) => DAY_ORDER.indexOf(a) - DAY_ORDER.indexOf(b)
  );

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
        {days.map((dayName) => {
          const dayMeals = mealsByDay[dayName];

          return (
            <div key={dayName} className="ds-card" style={{ padding: '1.5rem' }}>
              <div className="mb-4">
                <h3 className="ds-heading-sm m-0">{dayName}</h3>
              </div>

              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {dayMeals.map((meal) => (
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
