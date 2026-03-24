import { useState, useEffect } from 'react';
import type { Meal } from '../types';
import { mealService } from '../services/mealService';
import { MealPlanView } from '../components/meals/MealPlanView';
import { MealDetails } from '../components/meals/MealDetails';

export const MealsPage = () => {
  const [meals, setMeals] = useState<Meal[]>([]);
  const [selectedMeal, setSelectedMeal] = useState<Meal | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMealPlan();
  }, []);

  const loadMealPlan = async () => {
    try {
      setLoading(true);
      setError(null);
      const template = await mealService.getMealPlan();
      
      if (!template || !template.days || template.days.length === 0) {
        setMeals([]);
        setError('No meal plan configured yet. Complete onboarding to set up your meal plan.');
      } else {
        const flattenedMeals: Meal[] = [];
        
        template.days.forEach(day => {
          day.meals.forEach((slot, index) => {
            if (slot.primary_dish) {
              flattenedMeals.push({
                id: `${day.day_of_week}-${slot.meal_name}-${index}`,
                mealType: slot.meal_name.toLowerCase().replace('_', ' ') as any,
                dish: {
                  id: slot.primary_dish.id,
                  name: slot.primary_dish.name,
                  description: slot.primary_dish.cuisine_type || '', 
                  macros: {
                    calories: slot.primary_dish.calories,
                    protein: slot.primary_dish.protein_g,
                    carbs: slot.primary_dish.carbs_g,
                    fats: slot.primary_dish.fats_g
                  },
                  prepTime: slot.primary_dish.prep_time_minutes || 0,
                  cookTime: slot.primary_dish.cook_time_minutes || 0
                },
                scheduledTime: slot.scheduled_time.substring(0, 5), // 'HH:MM' format
                dayName: day.day_name
              });
            }
          });
        });
        
        setMeals(flattenedMeals);
      }
    } catch (err) {
      setError('Failed to load meal plan. Please try again.');
      console.error('Meal plan error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMealClick = (meal: Meal) => setSelectedMeal(meal);
  const handleCloseMealDetails = () => setSelectedMeal(null);

  return (
    <div style={{ background: 'var(--color-bg-primary)', minHeight: '100vh' }}>
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>Meals</h1>
            <p style={{ color: 'var(--color-text-muted)' }}>
              View your personalized meal plan
            </p>
          </div>
          <button onClick={loadMealPlan} className="ds-btn-primary">
            Refresh Plan
          </button>
        </div>

        {/* Error */}
        {error && (
          <div
            className="mb-6 px-4 py-3 rounded-lg"
            style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)', color: '#f87171' }}
          >
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div
              className="animate-spin rounded-full h-12 w-12"
              style={{ borderWidth: 3, borderColor: 'var(--color-violet)', borderTopColor: 'transparent' }}
            />
          </div>
        )}

        {/* Content */}
        {!loading && (
          <MealPlanView meals={meals} onMealClick={handleMealClick} />
        )}

        <MealDetails meal={selectedMeal} onClose={handleCloseMealDetails} />
      </div>
    </div>
  );
};
