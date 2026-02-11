import { useState } from 'react';
import type { NotificationPreference } from '../../types';

interface Step10Props {
  initialData?: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onBack: () => void;
}

const Step10Notifications = ({ initialData, onNext, onBack }: Step10Props) => {
  const [workoutReminders, setWorkoutReminders] = useState<boolean>(
    initialData?.notificationPreferences?.workoutReminders ?? true
  );
  const [mealReminders, setMealReminders] = useState<boolean>(
    initialData?.notificationPreferences?.mealReminders ?? true
  );
  const [hydrationReminders, setHydrationReminders] = useState<boolean>(
    initialData?.notificationPreferences?.hydrationReminders ?? true
  );
  const [motivationalMessages, setMotivationalMessages] = useState<boolean>(
    initialData?.notificationPreferences?.motivationalMessages ?? true
  );

  const handleSubmit = () => {
    const preferences: NotificationPreference = {
      workoutReminders,
      mealReminders,
      hydrationReminders,
      motivationalMessages,
    };

    onNext({ notificationPreferences: preferences });
  };

  const toggleOption = (
    current: boolean,
    setter: (value: boolean) => void
  ) => {
    setter(!current);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Notification Preferences
        </h2>
        <p className="text-gray-600">
          Choose which reminders you'd like to receive.
        </p>
      </div>

      <div className="space-y-4">
        {/* Workout Reminders */}
        <div
          onClick={() => toggleOption(workoutReminders, setWorkoutReminders)}
          className="flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all hover:border-gray-300"
        >
          <div className="flex-1">
            <div className="font-semibold text-gray-900">Workout Reminders</div>
            <div className="text-sm text-gray-600 mt-1">
              Get notified before your scheduled workout sessions
            </div>
          </div>
          <div className="ml-4">
            <div
              className={`w-12 h-6 rounded-full transition-colors ${
                workoutReminders ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <div
                className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${
                  workoutReminders ? 'translate-x-6' : 'translate-x-1'
                } mt-0.5`}
              />
            </div>
          </div>
        </div>

        {/* Meal Reminders */}
        <div
          onClick={() => toggleOption(mealReminders, setMealReminders)}
          className="flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all hover:border-gray-300"
        >
          <div className="flex-1">
            <div className="font-semibold text-gray-900">Meal Reminders</div>
            <div className="text-sm text-gray-600 mt-1">
              Get notified at your scheduled meal times
            </div>
          </div>
          <div className="ml-4">
            <div
              className={`w-12 h-6 rounded-full transition-colors ${
                mealReminders ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <div
                className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${
                  mealReminders ? 'translate-x-6' : 'translate-x-1'
                } mt-0.5`}
              />
            </div>
          </div>
        </div>

        {/* Hydration Reminders */}
        <div
          onClick={() => toggleOption(hydrationReminders, setHydrationReminders)}
          className="flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all hover:border-gray-300"
        >
          <div className="flex-1">
            <div className="font-semibold text-gray-900">Hydration Reminders</div>
            <div className="text-sm text-gray-600 mt-1">
              Regular reminders to drink water throughout the day
            </div>
          </div>
          <div className="ml-4">
            <div
              className={`w-12 h-6 rounded-full transition-colors ${
                hydrationReminders ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <div
                className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${
                  hydrationReminders ? 'translate-x-6' : 'translate-x-1'
                } mt-0.5`}
              />
            </div>
          </div>
        </div>

        {/* Motivational Messages */}
        <div
          onClick={() => toggleOption(motivationalMessages, setMotivationalMessages)}
          className="flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all hover:border-gray-300"
        >
          <div className="flex-1">
            <div className="font-semibold text-gray-900">Motivational Messages</div>
            <div className="text-sm text-gray-600 mt-1">
              Receive encouraging messages and tips
            </div>
          </div>
          <div className="ml-4">
            <div
              className={`w-12 h-6 rounded-full transition-colors ${
                motivationalMessages ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <div
                className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${
                  motivationalMessages ? 'translate-x-6' : 'translate-x-1'
                } mt-0.5`}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-sm text-yellow-800">
          💡 You can change these preferences anytime in your settings.
        </p>
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

export default Step10Notifications;
