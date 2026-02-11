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
      <div className="flex items-center justify-center p-8 text-gray-500">
        <p>No meals scheduled. Your meal plan will appear here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-900">Weekly Meal Plan</h2>
      
      <div className="grid gap-4">
        {dates.map((date) => {
          const dateMeals = mealsByDate[date];
          const dateObj = new Date(date);
          const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'long' });
          const dateStr = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

          return (
            <div key={date} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <div className="mb-3">
                <h3 className="text-lg font-semibold text-gray-900">{dayName}</h3>
                <p className="text-sm text-gray-500">{dateStr}</p>
              </div>

              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                {dateMeals.map((meal) => (
                  <button
                    key={meal.id}
                    onClick={() => onMealClick(meal)}
                    className="text-left p-3 rounded-lg border border-gray-200 hover:border-blue-500 hover:shadow-md transition-all"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-blue-600 uppercase">
                        {meal.mealType}
                      </span>
                      <span className="text-xs text-gray-500">{meal.scheduledTime}</span>
                    </div>
                    <h4 className="font-medium text-gray-900 mb-1">{meal.dish.name}</h4>
                    <div className="flex gap-2 text-xs text-gray-600">
                      <span>{meal.dish.macros.calories} cal</span>
                      <span>•</span>
                      <span>P: {meal.dish.macros.protein}g</span>
                      <span>•</span>
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
