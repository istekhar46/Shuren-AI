import { useState } from 'react';
import type { MealSchedule } from '../../types';

interface Step6Props {
  initialData?: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onBack: () => void;
}

const Step6MealSchedule = ({ initialData, onNext, onBack }: Step6Props) => {
  const [mealSchedules, setMealSchedules] = useState<MealSchedule[]>(
    initialData?.mealSchedule || []
  );
  const [error, setError] = useState<string>('');

  const mealTypes = ['breakfast', 'lunch', 'dinner', 'snack'] as const;

  const handleTimeChange = (mealType: string, time: string) => {
    const existing = mealSchedules.find((m) => m.mealType === mealType);
    if (existing) {
      setMealSchedules(
        mealSchedules.map((m) =>
          m.mealType === mealType ? { ...m, time } : m
        )
      );
    } else {
      setMealSchedules([
        ...mealSchedules,
        { mealType: mealType as MealSchedule['mealType'], time },
      ]);
    }
  };

  const handleRemoveMeal = (mealType: string) => {
    setMealSchedules(mealSchedules.filter((m) => m.mealType !== mealType));
  };

  const handleSubmit = () => {
    if (mealSchedules.length === 0) {
      setError('Please add at least one meal time');
      return;
    }

    // Validate all times are set
    const invalidMeals = mealSchedules.filter((m) => !m.time);
    if (invalidMeals.length > 0) {
      setError('Please set times for all meals');
      return;
    }

    setError('');
    onNext({ mealSchedule: mealSchedules });
  };

  const getMealTime = (mealType: string): string => {
    return mealSchedules.find((m) => m.mealType === mealType)?.time || '';
  };

  const isMealAdded = (mealType: string): boolean => {
    return mealSchedules.some((m) => m.mealType === mealType);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Meal Schedule
        </h2>
        <p className="text-gray-600">
          Set your preferred meal times. We'll use these for reminders and planning.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <div className="space-y-4">
        {mealTypes.map((mealType) => (
          <div
            key={mealType}
            className={`p-4 border-2 rounded-lg ${
              isMealAdded(mealType)
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-200'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-medium text-gray-900 capitalize">
                {mealType}
              </label>
              {isMealAdded(mealType) && (
                <button
                  onClick={() => handleRemoveMeal(mealType)}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Remove
                </button>
              )}
            </div>
            <input
              type="time"
              value={getMealTime(mealType)}
              onChange={(e) => handleTimeChange(mealType, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        ))}
      </div>

      {mealSchedules.length > 0 && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <h4 className="font-semibold text-gray-900 mb-2">Your Schedule:</h4>
          <div className="space-y-1 text-sm text-gray-700">
            {mealSchedules
              .sort((a, b) => a.time.localeCompare(b.time))
              .map((meal) => (
                <div key={meal.mealType} className="flex justify-between">
                  <span className="capitalize">{meal.mealType}:</span>
                  <span className="font-medium">{meal.time}</span>
                </div>
              ))}
          </div>
        </div>
      )}

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

export default Step6MealSchedule;
