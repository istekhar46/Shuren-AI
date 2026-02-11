import { useState } from 'react';
import type { HydrationPreference } from '../../types';

interface Step8Props {
  initialData?: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onBack: () => void;
}

const Step8Hydration = ({ initialData, onNext, onBack }: Step8Props) => {
  const [dailyGoal, setDailyGoal] = useState<string>(
    initialData?.hydrationPreferences?.dailyGoal?.toString() || '2.5'
  );
  const [reminderInterval, setReminderInterval] = useState<string>(
    initialData?.hydrationPreferences?.reminderInterval?.toString() || '120'
  );
  const [error, setError] = useState<string>('');

  const handleSubmit = () => {
    const goal = parseFloat(dailyGoal);
    if (!goal || goal < 0.5 || goal > 10) {
      setError('Daily goal must be between 0.5 and 10 liters');
      return;
    }

    const interval = parseInt(reminderInterval);
    if (!interval || interval < 30 || interval > 480) {
      setError('Reminder interval must be between 30 and 480 minutes');
      return;
    }

    const preferences: HydrationPreference = {
      dailyGoal: goal,
      reminderInterval: interval,
    };

    setError('');
    onNext({ hydrationPreferences: preferences });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Hydration Goals
        </h2>
        <p className="text-gray-600">
          Set your daily water intake goal and reminder preferences.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <div className="space-y-4">
        {/* Daily Goal */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Daily Water Goal (liters)
          </label>
          <input
            type="number"
            step="0.1"
            value={dailyGoal}
            onChange={(e) => setDailyGoal(e.target.value)}
            placeholder="e.g., 2.5"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-xs text-gray-500 mt-1">
            Recommended: 2-3 liters per day
          </p>
        </div>

        {/* Quick Presets */}
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => setDailyGoal('2')}
            className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
          >
            2L
          </button>
          <button
            onClick={() => setDailyGoal('2.5')}
            className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
          >
            2.5L
          </button>
          <button
            onClick={() => setDailyGoal('3')}
            className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
          >
            3L
          </button>
        </div>

        {/* Reminder Interval */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Reminder Interval (minutes)
          </label>
          <select
            value={reminderInterval}
            onChange={(e) => setReminderInterval(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="30">Every 30 minutes</option>
            <option value="60">Every hour</option>
            <option value="90">Every 90 minutes</option>
            <option value="120">Every 2 hours</option>
            <option value="180">Every 3 hours</option>
            <option value="240">Every 4 hours</option>
          </select>
        </div>

        {/* Info Box */}
        {dailyGoal && reminderInterval && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-2">Your Plan:</h4>
            <div className="text-sm text-gray-700 space-y-1">
              <div>
                Daily Goal: {dailyGoal} liters ({(parseFloat(dailyGoal) * 1000).toFixed(0)}ml)
              </div>
              <div>
                Reminders: Every {reminderInterval} minutes
              </div>
              <div>
                Approx. {Math.ceil((16 * 60) / parseInt(reminderInterval))} reminders during waking hours
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

export default Step8Hydration;
