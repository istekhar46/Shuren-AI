import { useState } from 'react';
import type { Goal } from '../../types';

interface Step2Props {
  initialData?: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onBack: () => void;
}

const Step2Goals = ({ initialData, onNext, onBack }: Step2Props) => {
  const [goals, setGoals] = useState<Goal[]>(initialData?.goals || []);
  const [selectedType, setSelectedType] = useState<string>('');
  const [targetWeight, setTargetWeight] = useState<string>('');
  const [targetDate, setTargetDate] = useState<string>('');
  const [error, setError] = useState<string>('');

  const goalTypes = [
    { value: 'fat_loss', label: 'Fat Loss', requiresWeight: true },
    { value: 'muscle_gain', label: 'Muscle Gain', requiresWeight: true },
    { value: 'general_fitness', label: 'General Fitness', requiresWeight: false },
  ];

  const handleAddGoal = () => {
    if (!selectedType) {
      setError('Please select a goal type');
      return;
    }

    const goalType = goalTypes.find((g) => g.value === selectedType);
    if (goalType?.requiresWeight && !targetWeight) {
      setError('Please enter a target weight');
      return;
    }

    const newGoal: Goal = {
      type: selectedType as Goal['type'],
      ...(targetWeight && { targetWeight: parseFloat(targetWeight) }),
      ...(targetDate && { targetDate }),
    };

    setGoals([...goals, newGoal]);
    setSelectedType('');
    setTargetWeight('');
    setTargetDate('');
    setError('');
  };

  const handleRemoveGoal = (index: number) => {
    setGoals(goals.filter((_, i) => i !== index));
  };

  const handleSubmit = () => {
    if (goals.length === 0) {
      setError('Please add at least one goal');
      return;
    }
    setError('');
    onNext({ goals });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          What are your fitness goals?
        </h2>
        <p className="text-gray-600">
          Add one or more goals to help us personalize your plan.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* Current Goals */}
      {goals.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-semibold text-gray-900">Your Goals:</h3>
          {goals.map((goal, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg"
            >
              <div>
                <span className="font-medium">
                  {goalTypes.find((g) => g.value === goal.type)?.label}
                </span>
                {goal.targetWeight && (
                  <span className="text-sm text-gray-600 ml-2">
                    Target: {goal.targetWeight} kg
                  </span>
                )}
                {goal.targetDate && (
                  <span className="text-sm text-gray-600 ml-2">
                    By: {new Date(goal.targetDate).toLocaleDateString()}
                  </span>
                )}
              </div>
              <button
                onClick={() => handleRemoveGoal(index)}
                className="text-red-600 hover:text-red-800"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add Goal Form */}
      <div className="space-y-4 p-4 border border-gray-200 rounded-lg">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Goal Type
          </label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Select a goal</option>
            {goalTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {selectedType &&
          goalTypes.find((g) => g.value === selectedType)?.requiresWeight && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Weight (kg)
              </label>
              <input
                type="number"
                value={targetWeight}
                onChange={(e) => setTargetWeight(e.target.value)}
                placeholder="e.g., 70"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          )}

        {selectedType && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Date (Optional)
            </label>
            <input
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        )}

        <button
          onClick={handleAddGoal}
          className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
        >
          Add Goal
        </button>
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

export default Step2Goals;
