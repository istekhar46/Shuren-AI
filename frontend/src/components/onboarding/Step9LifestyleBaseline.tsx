import { useState } from 'react';
import type { LifestyleBaseline } from '../../types';

interface Step9Props {
  initialData?: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onBack: () => void;
}

const Step9LifestyleBaseline = ({ initialData, onNext, onBack }: Step9Props) => {
  const [energyLevel, setEnergyLevel] = useState<string>(
    initialData?.lifestyleBaseline?.energyLevel || ''
  );
  const [stressLevel, setStressLevel] = useState<string>(
    initialData?.lifestyleBaseline?.stressLevel || ''
  );
  const [sleepQuality, setSleepQuality] = useState<string>(
    initialData?.lifestyleBaseline?.sleepQuality || ''
  );
  const [error, setError] = useState<string>('');

  const handleSubmit = () => {
    if (!energyLevel) {
      setError('Please select your energy level');
      return;
    }
    if (!stressLevel) {
      setError('Please select your stress level');
      return;
    }
    if (!sleepQuality) {
      setError('Please select your sleep quality');
      return;
    }

    const baseline: LifestyleBaseline = {
      energyLevel: energyLevel as LifestyleBaseline['energyLevel'],
      stressLevel: stressLevel as LifestyleBaseline['stressLevel'],
      sleepQuality: sleepQuality as LifestyleBaseline['sleepQuality'],
    };

    setError('');
    onNext({ lifestyleBaseline: baseline });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Lifestyle Baseline
        </h2>
        <p className="text-gray-600">
          Help us understand your current lifestyle to create a realistic plan.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <div className="space-y-6">
        {/* Energy Level */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Current Energy Level
          </label>
          <div className="space-y-2">
            {[
              { value: 'low', label: 'Low', description: 'Often tired, low motivation' },
              { value: 'medium', label: 'Medium', description: 'Moderate energy, some ups and downs' },
              { value: 'high', label: 'High', description: 'Consistently energetic and motivated' },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => setEnergyLevel(option.value)}
                className={`w-full p-3 text-left border-2 rounded-lg transition-all ${
                  energyLevel === option.value
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-semibold text-gray-900">{option.label}</div>
                <div className="text-sm text-gray-600">{option.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Stress Level */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Current Stress Level
          </label>
          <div className="space-y-2">
            {[
              { value: 'low', label: 'Low', description: 'Relaxed, minimal daily stress' },
              { value: 'medium', label: 'Medium', description: 'Manageable stress, some pressure' },
              { value: 'high', label: 'High', description: 'High stress, feeling overwhelmed' },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => setStressLevel(option.value)}
                className={`w-full p-3 text-left border-2 rounded-lg transition-all ${
                  stressLevel === option.value
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-semibold text-gray-900">{option.label}</div>
                <div className="text-sm text-gray-600">{option.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Sleep Quality */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Sleep Quality
          </label>
          <div className="space-y-2">
            {[
              { value: 'poor', label: 'Poor', description: 'Trouble sleeping, often tired' },
              { value: 'fair', label: 'Fair', description: 'Inconsistent sleep, some restless nights' },
              { value: 'good', label: 'Good', description: 'Generally sleep well most nights' },
              { value: 'excellent', label: 'Excellent', description: 'Consistently great sleep' },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => setSleepQuality(option.value)}
                className={`w-full p-3 text-left border-2 rounded-lg transition-all ${
                  sleepQuality === option.value
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-semibold text-gray-900">{option.label}</div>
                <div className="text-sm text-gray-600">{option.description}</div>
              </button>
            ))}
          </div>
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

export default Step9LifestyleBaseline;
