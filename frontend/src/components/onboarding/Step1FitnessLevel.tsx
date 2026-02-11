import { useState } from 'react';

interface Step1Props {
  initialData?: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onBack: () => void;
}

const Step1FitnessLevel = ({ initialData, onNext, onBack }: Step1Props) => {
  const [fitnessLevel, setFitnessLevel] = useState<string>(
    initialData?.fitnessLevel || ''
  );
  const [error, setError] = useState<string>('');

  const handleSubmit = () => {
    if (!fitnessLevel) {
      setError('Please select your fitness level');
      return;
    }
    setError('');
    onNext({ fitnessLevel });
  };

  const levels = [
    {
      value: 'beginner',
      title: 'Beginner',
      description: 'New to fitness or returning after a long break',
    },
    {
      value: 'intermediate',
      title: 'Intermediate',
      description: 'Regular exercise routine for 6+ months',
    },
    {
      value: 'advanced',
      title: 'Advanced',
      description: 'Consistent training for 2+ years with clear goals',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          What's your fitness level?
        </h2>
        <p className="text-gray-600">
          This helps us create a workout plan that matches your current abilities.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <div className="space-y-3">
        {levels.map((level) => (
          <button
            key={level.value}
            onClick={() => setFitnessLevel(level.value)}
            className={`w-full p-4 text-left border-2 rounded-lg transition-all ${
              fitnessLevel === level.value
                ? 'border-blue-600 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="font-semibold text-gray-900">{level.title}</div>
            <div className="text-sm text-gray-600 mt-1">{level.description}</div>
          </button>
        ))}
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

export default Step1FitnessLevel;
