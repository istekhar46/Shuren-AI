import { useEffect, useState } from 'react';

interface Step11Props {
  initialData?: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onBack: () => void;
  allStepData: Record<number, Record<string, any>>;
}

const Step11Review = ({ onNext, onBack, allStepData }: Step11Props) => {
  const [reviewData, setReviewData] = useState<Record<string, any>>({});

  useEffect(() => {
    // Compile all step data for review
    const compiled = Object.values(allStepData).reduce(
      (acc, stepData) => ({ ...acc, ...stepData }),
      {}
    );
    setReviewData(compiled);
  }, [allStepData]);

  const handleSubmit = () => {
    onNext({});
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Review Your Profile
        </h2>
        <p className="text-gray-600">
          Please review your information before completing onboarding.
        </p>
      </div>

      <div className="space-y-4">
        {/* Fitness Level */}
        {reviewData.fitnessLevel && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Fitness Level</h3>
            <p className="text-gray-700 capitalize">{reviewData.fitnessLevel}</p>
          </div>
        )}

        {/* Goals */}
        {reviewData.goals && reviewData.goals.length > 0 && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Goals</h3>
            <ul className="space-y-1 text-gray-700">
              {reviewData.goals.map((goal: any, index: number) => (
                <li key={index}>
                  • {goal.type.replace('_', ' ')}
                  {goal.targetWeight && ` - Target: ${goal.targetWeight}kg`}
                  {goal.targetDate && ` by ${new Date(goal.targetDate).toLocaleDateString()}`}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Physical Constraints */}
        {reviewData.physicalConstraints && reviewData.physicalConstraints.length > 0 && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Physical Constraints</h3>
            <ul className="space-y-1 text-gray-700">
              {reviewData.physicalConstraints.map((constraint: any, index: number) => (
                <li key={index}>
                  • {constraint.type}: {constraint.description}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Dietary Preferences */}
        {reviewData.dietaryPreferences && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Dietary Preferences</h3>
            <div className="text-gray-700 space-y-1">
              <p>Diet Type: {reviewData.dietaryPreferences.dietType}</p>
              {reviewData.dietaryPreferences.allergies?.length > 0 && (
                <p>Allergies: {reviewData.dietaryPreferences.allergies.join(', ')}</p>
              )}
              {reviewData.dietaryPreferences.dislikes?.length > 0 && (
                <p>Dislikes: {reviewData.dietaryPreferences.dislikes.join(', ')}</p>
              )}
            </div>
          </div>
        )}

        {/* Meal Plan */}
        {reviewData.mealPlan && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Meal Plan</h3>
            <div className="text-gray-700 space-y-1">
              <p>Daily Calories: {reviewData.mealPlan.dailyCalories}</p>
              <p>
                Macros: {reviewData.mealPlan.macros.protein}g protein,{' '}
                {reviewData.mealPlan.macros.carbs}g carbs, {reviewData.mealPlan.macros.fats}g fats
              </p>
              <p>Meals Per Day: {reviewData.mealPlan.mealsPerDay}</p>
            </div>
          </div>
        )}

        {/* Meal Schedule */}
        {reviewData.mealSchedule && reviewData.mealSchedule.length > 0 && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Meal Schedule</h3>
            <ul className="space-y-1 text-gray-700">
              {reviewData.mealSchedule.map((meal: any, index: number) => (
                <li key={index} className="capitalize">
                  • {meal.mealType}: {meal.time}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Workout Schedule */}
        {reviewData.workoutSchedule && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Workout Schedule</h3>
            <div className="text-gray-700 space-y-1">
              <p>Days Per Week: {reviewData.workoutSchedule.daysPerWeek}</p>
              <p>
                Preferred Days:{' '}
                {reviewData.workoutSchedule.preferredDays.map((d: string) => d).join(', ')}
              </p>
              <p>Preferred Time: {reviewData.workoutSchedule.preferredTime}</p>
              <p>Session Duration: {reviewData.workoutSchedule.sessionDuration} minutes</p>
            </div>
          </div>
        )}

        {/* Hydration */}
        {reviewData.hydrationPreferences && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Hydration</h3>
            <div className="text-gray-700 space-y-1">
              <p>Daily Goal: {reviewData.hydrationPreferences.dailyGoal} liters</p>
              <p>Reminder Interval: {reviewData.hydrationPreferences.reminderInterval} minutes</p>
            </div>
          </div>
        )}

        {/* Lifestyle Baseline */}
        {reviewData.lifestyleBaseline && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Lifestyle Baseline</h3>
            <div className="text-gray-700 space-y-1">
              <p>Energy Level: {reviewData.lifestyleBaseline.energyLevel}</p>
              <p>Stress Level: {reviewData.lifestyleBaseline.stressLevel}</p>
              <p>Sleep Quality: {reviewData.lifestyleBaseline.sleepQuality}</p>
            </div>
          </div>
        )}

        {/* Notifications */}
        {reviewData.notificationPreferences && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Notification Preferences</h3>
            <div className="text-gray-700 space-y-1">
              <p>
                Workout Reminders:{' '}
                {reviewData.notificationPreferences.workoutReminders ? 'Enabled' : 'Disabled'}
              </p>
              <p>
                Meal Reminders:{' '}
                {reviewData.notificationPreferences.mealReminders ? 'Enabled' : 'Disabled'}
              </p>
              <p>
                Hydration Reminders:{' '}
                {reviewData.notificationPreferences.hydrationReminders ? 'Enabled' : 'Disabled'}
              </p>
              <p>
                Motivational Messages:{' '}
                {reviewData.notificationPreferences.motivationalMessages ? 'Enabled' : 'Disabled'}
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          ℹ️ You can edit your profile later from the dashboard.
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

export default Step11Review;
