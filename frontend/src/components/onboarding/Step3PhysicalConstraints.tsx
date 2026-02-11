import { useState } from 'react';
import type { PhysicalConstraint } from '../../types';

interface Step3Props {
  initialData?: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onBack: () => void;
}

const Step3PhysicalConstraints = ({ initialData, onNext, onBack }: Step3Props) => {
  const [constraints, setConstraints] = useState<PhysicalConstraint[]>(
    initialData?.physicalConstraints || []
  );
  const [selectedType, setSelectedType] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [error, setError] = useState<string>('');

  const constraintTypes = [
    { value: 'equipment', label: 'Equipment Limitation' },
    { value: 'injury', label: 'Injury or Pain' },
    { value: 'limitation', label: 'Physical Limitation' },
  ];

  const handleAddConstraint = () => {
    if (!selectedType) {
      setError('Please select a constraint type');
      return;
    }
    if (!description.trim()) {
      setError('Please provide a description');
      return;
    }

    const newConstraint: PhysicalConstraint = {
      type: selectedType as PhysicalConstraint['type'],
      description: description.trim(),
    };

    setConstraints([...constraints, newConstraint]);
    setSelectedType('');
    setDescription('');
    setError('');
  };

  const handleRemoveConstraint = (index: number) => {
    setConstraints(constraints.filter((_, i) => i !== index));
  };

  const handleSubmit = () => {
    setError('');
    onNext({ physicalConstraints: constraints });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Any physical constraints?
        </h2>
        <p className="text-gray-600">
          Tell us about equipment limitations, injuries, or physical restrictions.
          Skip if none apply.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* Current Constraints */}
      {constraints.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-semibold text-gray-900">Your Constraints:</h3>
          {constraints.map((constraint, index) => (
            <div
              key={index}
              className="flex items-start justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg"
            >
              <div>
                <span className="font-medium">
                  {constraintTypes.find((c) => c.value === constraint.type)?.label}
                </span>
                <p className="text-sm text-gray-600 mt-1">{constraint.description}</p>
              </div>
              <button
                onClick={() => handleRemoveConstraint(index)}
                className="text-red-600 hover:text-red-800 ml-4"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add Constraint Form */}
      <div className="space-y-4 p-4 border border-gray-200 rounded-lg">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Constraint Type
          </label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Select a type</option>
            {constraintTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., No gym equipment, only bodyweight exercises"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <button
          onClick={handleAddConstraint}
          className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
        >
          Add Constraint
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

export default Step3PhysicalConstraints;
