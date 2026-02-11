import { useState, useEffect } from 'react';
import type { Meal } from '../types';
import { mealService } from '../services/mealService';
import { MealPlanView } from '../components/meals/MealPlanView';
import { MealDetails } from '../components/meals/MealDetails';
import { DishBrowser } from '../components/meals/DishBrowser';
import { ShoppingList } from '../components/meals/ShoppingList';

type ViewMode = 'plan' | 'browse' | 'shopping';

export const MealsPage = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('plan');
  const [meals, setMeals] = useState<Meal[]>([]);
  const [selectedMeal, setSelectedMeal] = useState<Meal | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Date range for meal plan and shopping list
  const [startDate, setStartDate] = useState(() => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => {
    const today = new Date();
    const nextWeek = new Date(today);
    nextWeek.setDate(today.getDate() + 7);
    return nextWeek.toISOString().split('T')[0];
  });

  useEffect(() => {
    if (viewMode === 'plan') {
      loadMealPlan();
    }
  }, [viewMode]);

  const loadMealPlan = async () => {
    try {
      setLoading(true);
      setError(null);
      const mealPlan = await mealService.getMealPlan();
      
      if (!mealPlan) {
        setMeals([]);
        setError('No meal plan configured yet. Complete onboarding to set up your meal plan.');
      } else {
        // Meal plan exists but doesn't contain actual meals
        // The backend only returns nutritional targets, not individual meals
        setMeals([]);
      }
    } catch (err) {
      setError('Failed to load meal plan. Please try again.');
      console.error('Meal plan error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMealClick = (meal: Meal) => {
    setSelectedMeal(meal);
  };

  const handleCloseMealDetails = () => {
    setSelectedMeal(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Meals</h1>
          <p className="text-gray-600">
            View your meal plan, browse dishes, and generate shopping lists
          </p>
        </div>

        {/* View Mode Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="flex gap-8">
            <button
              onClick={() => setViewMode('plan')}
              className={`pb-4 px-1 border-b-2 font-medium transition-colors ${
                viewMode === 'plan'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Meal Plan
            </button>
            <button
              onClick={() => setViewMode('browse')}
              className={`pb-4 px-1 border-b-2 font-medium transition-colors ${
                viewMode === 'browse'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Browse Dishes
            </button>
            <button
              onClick={() => setViewMode('shopping')}
              className={`pb-4 px-1 border-b-2 font-medium transition-colors ${
                viewMode === 'shopping'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Shopping List
            </button>
          </nav>
        </div>

        {/* Date Range Selector (for Plan and Shopping views) */}
        {(viewMode === 'plan' || viewMode === 'shopping') && (
          <div className="mb-6 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <label htmlFor="startDate" className="text-sm font-medium text-gray-700">
                  From:
                </label>
                <input
                  type="date"
                  id="startDate"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="flex items-center gap-2">
                <label htmlFor="endDate" className="text-sm font-medium text-gray-700">
                  To:
                </label>
                <input
                  type="date"
                  id="endDate"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              {viewMode === 'plan' && (
                <button
                  onClick={loadMealPlan}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Refresh
                </button>
              )}
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        )}

        {/* Content based on view mode */}
        {!loading && (
          <>
            {viewMode === 'plan' && (
              <MealPlanView meals={meals} onMealClick={handleMealClick} />
            )}

            {viewMode === 'browse' && <DishBrowser />}

            {viewMode === 'shopping' && (
              <ShoppingList startDate={startDate} endDate={endDate} />
            )}
          </>
        )}

        {/* Meal Details Modal */}
        <MealDetails meal={selectedMeal} onClose={handleCloseMealDetails} />
      </div>
    </div>
  );
};
