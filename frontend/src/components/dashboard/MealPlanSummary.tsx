import React from 'react';
import type { UserProfile } from '../../types';

interface MealPlanSummaryProps {
  profile: UserProfile;
}

export const MealPlanSummary: React.FC<MealPlanSummaryProps> = ({ profile }) => {
  const { mealPlan } = profile;

  // Handle case where meal plan is not set
  if (!mealPlan || !mealPlan.macros) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Meal Plan Summary</h2>
        <p className="text-sm text-gray-500">No meal plan configured yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Meal Plan Summary</h2>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-600">Daily Calories:</span>
          <span className="text-sm text-gray-900 font-semibold">{mealPlan.dailyCalories || 0} kcal</span>
        </div>

        <div className="border-t pt-3">
          <p className="text-sm font-medium text-gray-600 mb-2">Macros:</p>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Protein:</span>
              <span className="text-sm text-gray-900">{mealPlan.macros.protein || 0}g</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Carbs:</span>
              <span className="text-sm text-gray-900">{mealPlan.macros.carbs || 0}g</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Fats:</span>
              <span className="text-sm text-gray-900">{mealPlan.macros.fats || 0}g</span>
            </div>
          </div>
        </div>

        <div className="border-t pt-3">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-600">Meals Per Day:</span>
            <span className="text-sm text-gray-900">{mealPlan.mealsPerDay || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
