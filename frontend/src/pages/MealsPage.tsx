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
    if (viewMode === 'plan') loadMealPlan();
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
        setMeals([]);
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

  const tabs: { key: ViewMode; label: string }[] = [
    { key: 'plan', label: 'Meal Plan' },
    { key: 'browse', label: 'Browse Dishes' },
    { key: 'shopping', label: 'Shopping List' },
  ];

  return (
    <div style={{ background: 'var(--color-bg-primary)', minHeight: '100vh' }}>
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>Meals</h1>
          <p style={{ color: 'var(--color-text-muted)' }}>
            View your meal plan, browse dishes, and generate shopping lists
          </p>
        </div>

        {/* View Mode Tabs */}
        <div className="mb-6" style={{ borderBottom: '1px solid var(--color-border)' }}>
          <nav className="flex gap-8">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setViewMode(tab.key)}
                className="pb-4 px-1 font-medium transition-colors"
                style={{
                  borderBottom: `2px solid ${viewMode === tab.key ? 'var(--color-violet)' : 'transparent'}`,
                  color: viewMode === tab.key ? 'var(--color-violet)' : 'var(--color-text-muted)',
                }}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Date Range Selector */}
        {(viewMode === 'plan' || viewMode === 'shopping') && (
          <div className="ds-card mb-6">
            <div className="flex flex-wrap items-center gap-4">
              {[
                { id: 'startDate', label: 'From:', value: startDate, onChange: setStartDate },
                { id: 'endDate', label: 'To:', value: endDate, onChange: setEndDate },
              ].map((picker) => (
                <div key={picker.id} className="flex items-center gap-2">
                  <label htmlFor={picker.id} className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                    {picker.label}
                  </label>
                  <input
                    type="date"
                    id={picker.id}
                    value={picker.value}
                    onChange={(e) => picker.onChange(e.target.value)}
                    className="px-3 py-2 rounded-lg focus:ring-2 focus:ring-[var(--color-violet)] focus:border-transparent"
                    style={{
                      background: 'var(--color-bg-surface)',
                      border: '1px solid var(--color-border)',
                      color: 'var(--color-text-primary)',
                    }}
                  />
                </div>
              ))}
              {viewMode === 'plan' && (
                <button onClick={loadMealPlan} className="ds-btn-primary">
                  Refresh
                </button>
              )}
            </div>
          </div>
        )}

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
          <>
            {viewMode === 'plan' && <MealPlanView meals={meals} onMealClick={handleMealClick} />}
            {viewMode === 'browse' && <DishBrowser />}
            {viewMode === 'shopping' && <ShoppingList startDate={startDate} endDate={endDate} />}
          </>
        )}

        <MealDetails meal={selectedMeal} onClose={handleCloseMealDetails} />
      </div>
    </div>
  );
};
