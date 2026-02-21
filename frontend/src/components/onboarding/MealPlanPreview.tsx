import React from 'react';
import type { OnboardingMealPlan } from '../../types/onboarding.types';

interface MealPlanPreviewProps {
  plan: OnboardingMealPlan;
}

/**
 * MealPlanPreview Component
 * 
 * Displays meal plan details in a structured, readable format:
 * - Calorie target
 * - Macro breakdown (protein, carbs, fats)
 * - Sample meals with nutrition info
 * - Meal timing suggestions
 * - Dietary restrictions noted
 * 
 * Requirements: US-3, AC-3.2
 */
export const MealPlanPreview: React.FC<MealPlanPreviewProps> = ({ plan }) => {
  /**
   * Calculate macro percentages
   */
  const totalMacroCalories =
    plan.macros.protein_g * 4 + plan.macros.carbs_g * 4 + plan.macros.fats_g * 9;
  const proteinPercent = Math.round((plan.macros.protein_g * 4 / totalMacroCalories) * 100);
  const carbsPercent = Math.round((plan.macros.carbs_g * 4 / totalMacroCalories) * 100);
  const fatsPercent = Math.round((plan.macros.fats_g * 9 / totalMacroCalories) * 100);

  return (
    <div className="space-y-6">
      {/* Plan Summary */}
      <div className="bg-gradient-to-r from-orange-50 to-yellow-50 rounded-lg p-5 border border-orange-200">
        <h3 className="text-lg font-bold text-gray-900 mb-3">Plan Overview</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">🍽️</span>
            <div>
              <p className="text-xs text-gray-600">Diet Type</p>
              <p className="text-sm font-semibold text-gray-900 capitalize">
                {plan.diet_type}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-2xl">🔥</span>
            <div>
              <p className="text-xs text-gray-600">Daily Calories</p>
              <p className="text-sm font-semibold text-gray-900">
                {plan.daily_calories} kcal
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-2xl">📊</span>
            <div>
              <p className="text-xs text-gray-600">Meal Frequency</p>
              <p className="text-sm font-semibold text-gray-900">
                {plan.meal_frequency} meals/day
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Macro Breakdown */}
      <div className="bg-white rounded-lg border-2 border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-5 py-3">
          <h3 className="text-lg font-bold text-white flex items-center">
            <span className="text-xl mr-2">📊</span>
            Macro Breakdown
          </h3>
        </div>
        <div className="p-5">
          {/* Macro Bars */}
          <div className="space-y-4 mb-4">
            {/* Protein */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-gray-700">Protein</span>
                <span className="text-sm font-bold text-blue-600">
                  {plan.macros.protein_g}g ({proteinPercent}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-blue-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${proteinPercent}%` }}
                />
              </div>
            </div>

            {/* Carbs */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-gray-700">Carbs</span>
                <span className="text-sm font-bold text-green-600">
                  {plan.macros.carbs_g}g ({carbsPercent}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-green-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${carbsPercent}%` }}
                />
              </div>
            </div>

            {/* Fats */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-gray-700">Fats</span>
                <span className="text-sm font-bold text-yellow-600">
                  {plan.macros.fats_g}g ({fatsPercent}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-yellow-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${fatsPercent}%` }}
                />
              </div>
            </div>
          </div>

          {/* Macro Summary */}
          <div className="grid grid-cols-3 gap-3 mt-4">
            <div className="bg-blue-50 rounded-lg p-3 text-center border border-blue-200">
              <p className="text-2xl font-bold text-blue-600">{plan.macros.protein_g}g</p>
              <p className="text-xs text-blue-800 font-medium">Protein</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3 text-center border border-green-200">
              <p className="text-2xl font-bold text-green-600">{plan.macros.carbs_g}g</p>
              <p className="text-xs text-green-800 font-medium">Carbs</p>
            </div>
            <div className="bg-yellow-50 rounded-lg p-3 text-center border border-yellow-200">
              <p className="text-2xl font-bold text-yellow-600">{plan.macros.fats_g}g</p>
              <p className="text-xs text-yellow-800 font-medium">Fats</p>
            </div>
          </div>
        </div>
      </div>

      {/* Sample Meals */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-gray-900 flex items-center">
          <span className="text-xl mr-2">🍴</span>
          Sample Meals
        </h3>
        {plan.sample_meals.map((meal) => (
          <div
            key={meal.meal_number}
            className="bg-white rounded-lg border-2 border-gray-200 overflow-hidden hover:border-orange-300 transition-colors duration-200"
          >
            {/* Meal Header */}
            <div className="bg-gradient-to-r from-orange-500 to-red-500 px-5 py-3">
              <div className="flex justify-between items-center">
                <h4 className="text-lg font-bold text-white">
                  Meal {meal.meal_number}: {meal.name}
                </h4>
                <span className="text-sm font-semibold text-white bg-white/20 px-3 py-1 rounded-full">
                  {meal.calories} kcal
                </span>
              </div>
            </div>

            {/* Meal Details */}
            <div className="p-5">
              {/* Nutrition Info */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="text-center">
                  <p className="text-xs text-gray-600 mb-1">Protein</p>
                  <p className="text-lg font-bold text-blue-600">{meal.protein_g}g</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-600 mb-1">Carbs</p>
                  <p className="text-lg font-bold text-green-600">{meal.carbs_g}g</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-600 mb-1">Fats</p>
                  <p className="text-lg font-bold text-yellow-600">{meal.fats_g}g</p>
                </div>
              </div>

              {/* Foods List */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-xs font-semibold text-gray-700 mb-2">Foods:</p>
                <ul className="space-y-1">
                  {meal.foods.map((food, index) => (
                    <li key={index} className="text-sm text-gray-800 flex items-start">
                      <span className="text-orange-500 mr-2">•</span>
                      <span>{food}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Meal Timing Note */}
      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
        <p className="text-sm text-blue-900">
          <span className="font-semibold">💡 Tip:</span> Space your meals evenly throughout the
          day for optimal energy levels and metabolism. Adjust timing based on your workout
          schedule and personal preferences.
        </p>
      </div>

      {/* Summary Footer */}
      <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
        <p className="text-sm text-orange-900">
          <span className="font-semibold">Total:</span> {plan.meal_frequency} meals providing{' '}
          {plan.daily_calories} calories per day
        </p>
      </div>
    </div>
  );
};
