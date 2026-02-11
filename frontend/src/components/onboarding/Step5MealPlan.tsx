import { useState } from 'react';
import type { MealPlan } from '../../types';

interface Step5Props {
  initialData?: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onBack: () => void;
}

const Step5MealPlan = ({ initialData, onNext, onBack }: Step5Props) => {
  const [dailyCalories, setDailyCalories] = useState<string>(
    initialData?.mealPlan?.dailyCalories?.toString() || ''
  );
  const [protein, setProtein] = useState<string>(
    initialData?.mealPlan?.macros?.protein?.toString() || ''
  );
  const [carbs, setCarbs] = useState<string>(
    initialData?.mealPlan?.macros?.carbs?.toString() || ''
  );
  const [fats, setFats] = useState<string>(
    initialData?.mealPlan?.macros?.fats?.toString() || ''
  );
  const [mealsPerDay, setMealsPerDay] = useState<string>(
    initialData?.mealPlan?.mealsPerDay?.toString() || '3'
  );
  const [error, setError] = useState<string>('');

  const handleSubmit = () => {
    if (!dailyCalories || parseFloat(dailyCalories) <= 0) {
      setError('Please enter a valid daily calorie target');
      return;
    }
    if (!protein || parseFloat(protein) <= 0) {
      setError('Please enter a valid protein target');
      return;
    }
    if (!carbs || parseFloat(carbs) <= 0) {
      setError('Please enter a valid carbs target');
      return;
    }
    if (!fats || parseFloat(fats) <= 0) {
      setError('Please enter a valid fats target');
      return;
    }
    if (!mealsPerDay || parseInt(mealsPerDay) < 1 || parseInt(mealsPerDay) > 6) {
      setError('Meals per day must be between 1 and 6');
      return;
    }

    const mealPlan: MealPlan = {
      dailyCalories: parseFloat(dailyCalories),
      macros: {
        protein: parseFloat(protein),
        carbs: parseFloat(carbs),
        fats: parseFloat(fats),
      },
      mealsPerDay: parseInt(mealsPerDay),
    };

    setError('');
    onNext({ mealPlan });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Meal Plan Configuration
        </h2>
        <p className="text-gray-600">
          Set your daily nutritional targets. We'll create meal plans to match these goals.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <div className="space-y-4">
        {/* Daily Calories */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Daily Calorie Target
          </label>
          <input
            type="number"
            value={dailyCalories}
            onChange={(e) => setDailyCalories(e.target.value)}
            placeholder="e.g., 2000"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-xs text-gray-500 mt-1">
            Typical range: 1500-3000 calories
          </p>
        </div>

        {/* Macros */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Protein (g)
            </label>
            <input
              type="number"
              value={protein}
              onChange={(e) => setProtein(e.target.value)}
              placeholder="e.g., 150"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Carbs (g)
            </label>
            <input
              type="number"
              value={carbs}
              onChange={(e) => setCarbs(e.target.value)}
              placeholder="e.g., 200"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Fats (g)
            </label>
            <input
              type="number"
              value={fats}
              onChange={(e) => setFats(e.target.value)}
              placeholder="e.g., 60"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Meals Per Day */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Meals Per Day
          </label>
          <select
            value={mealsPerDay}
            onChange={(e) => setMealsPerDay(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="2">2 meals</option>
            <option value="3">3 meals</option>
            <option value="4">4 meals</option>
            <option value="5">5 meals</option>
            <option value="6">6 meals</option>
          </select>
        </div>

        {/* Macro Breakdown Info */}
        {dailyCalories && protein && carbs && fats && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-2">Macro Breakdown:</h4>
            <div className="text-sm text-gray-700 space-y-1">
              <div>
                Protein: {protein}g × 4 cal/g ={' '}
                {parseFloat(protein) * 4} calories (
                {((parseFloat(protein) * 4) / parseFloat(dailyCalories) * 100).toFixed(1)}%)
              </div>
              <div>
                Carbs: {carbs}g × 4 cal/g ={' '}
                {parseFloat(carbs) * 4} calories (
                {((parseFloat(carbs) * 4) / parseFloat(dailyCalories) * 100).toFixed(1)}%)
              </div>
              <div>
                Fats: {fats}g × 9 cal/g ={' '}
                {parseFloat(fats) * 9} calories (
                {((parseFloat(fats) * 9) / parseFloat(dailyCalories) * 100).toFixed(1)}%)
              </div>
              <div className="pt-2 border-t border-blue-300 font-semibold">
                Total: {parseFloat(protein) * 4 + parseFloat(carbs) * 4 + parseFloat(fats) * 9} calories
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-between pt-4">
        <button
          onClick={onBack}
          className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={handleSubmit}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default Step5MealPlan;
