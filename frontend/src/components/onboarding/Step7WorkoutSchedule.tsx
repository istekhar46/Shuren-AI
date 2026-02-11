import { useState } from 'react';
import type { WorkoutSchedule } from '../../types';

interface Step7Props {
  initialData?: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onBack: () => void;
}

const Step7WorkoutSchedule = ({ initialData, onNext, onBack }: Step7Props) => {
  const [daysPerWeek, setDaysPerWeek] = useState<string>(
    initialData?.workoutSchedule?.daysPerWeek?.toString() || '3'
  );
  const [preferredDays, setPreferredDays] = useState<string[]>(
    initialData?.workoutSchedule?.preferredDays || []
  );
  const [preferredTime, setPreferredTime] = useState<string>(
    initialData?.workoutSchedule?.preferredTime || ''
  );
  const [sessionDuration, setSessionDuration] = useState<string>(
    initialData?.workoutSchedule?.sessionDuration?.toString() || '60'
  );
  const [error, setError] = useState<string>('');

  const weekDays = [
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
    'sunday',
  ];

  const handleDayToggle = (day: string) => {
    if (preferredDays.includes(day)) {
      setPreferredDays(preferredDays.filter((d) => d !== day));
    } else {
      setPreferredDays([...preferredDays, day]);
    }
  };

  const handleSubmit = () => {
    const days = parseInt(daysPerWeek);
    if (!days || days < 1 || days > 7) {
      setError('Days per week must be between 1 and 7');
      return;
    }
    if (preferredDays.length === 0) {
      setError('Please select at least one preferred day');
      return;
    }
    if (preferredDays.length < days) {
      setError(`Please select at least ${days} days to match your weekly goal`);
      return;
    }
    if (!preferredTime) {
      setError('Please select a preferred workout time');
      return;
    }
    const duration = parseInt(sessionDuration);
    if (!duration || duration < 15 || duration > 180) {
      setError('Session duration must be between 15 and 180 minutes');
      return;
    }

    const schedule: WorkoutSchedule = {
      daysPerWeek: days,
      preferredDays,
      preferredTime,
      sessionDuration: duration,
    };

    setError('');
    onNext({ workoutSchedule: schedule });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Workout Schedule
        </h2>
        <p className="text-gray-600">
          Set your workout frequency and preferred times.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <div className="space-y-4">
        {/* Days Per Week */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Workouts Per Week
          </label>
          <select
            value={daysPerWeek}
            onChange={(e) => setDaysPerWeek(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {[1, 2, 3, 4, 5, 6, 7].map((num) => (
              <option key={num} value={num}>
                {num} {num === 1 ? 'day' : 'days'} per week
              </option>
            ))}
          </select>
        </div>

        {/* Preferred Days */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Preferred Days
          </label>
          <div className="grid grid-cols-2 gap-2">
            {weekDays.map((day) => (
              <button
                key={day}
                onClick={() => handleDayToggle(day)}
                className={`p-3 border-2 rounded-lg capitalize transition-all ${
                  preferredDays.includes(day)
                    ? 'border-blue-600 bg-blue-50 text-blue-900'
                    : 'border-gray-200 text-gray-700 hover:border-gray-300'
                }`}
              >
                {day}
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Select at least {daysPerWeek} {parseInt(daysPerWeek) === 1 ? 'day' : 'days'}
          </p>
        </div>

        {/* Preferred Time */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Preferred Workout Time
          </label>
          <input
            type="time"
            value={preferredTime}
            onChange={(e) => setPreferredTime(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Session Duration */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Session Duration (minutes)
          </label>
          <input
            type="number"
            value={sessionDuration}
            onChange={(e) => setSessionDuration(e.target.value)}
            placeholder="e.g., 60"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-xs text-gray-500 mt-1">
            Typical range: 30-90 minutes
          </p>
        </div>
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

export default Step7WorkoutSchedule;
