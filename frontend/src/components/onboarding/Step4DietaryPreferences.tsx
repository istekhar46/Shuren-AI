import { useState } from 'react';
import type { DietaryPreference } from '../../types';

interface Step4Props {
  initialData?: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onBack: () => void;
}

const Step4DietaryPreferences = ({ initialData, onNext, onBack }: Step4Props) => {
  const [dietType, setDietType] = useState<string>(
    initialData?.dietaryPreferences?.dietType || ''
  );
  const [allergies, setAllergies] = useState<string[]>(
    initialData?.dietaryPreferences?.allergies || []
  );
  const [dislikes, setDislikes] = useState<string[]>(
    initialData?.dietaryPreferences?.dislikes || []
  );
  const [allergyInput, setAllergyInput] = useState<string>('');
  const [dislikeInput, setDislikeInput] = useState<string>('');
  const [error, setError] = useState<string>('');

  const dietTypes = [
    { value: 'omnivore', label: 'Omnivore', description: 'Eat all types of food' },
    { value: 'vegetarian', label: 'Vegetarian', description: 'No meat or fish' },
    { value: 'vegan', label: 'Vegan', description: 'No animal products' },
    { value: 'pescatarian', label: 'Pescatarian', description: 'Fish but no meat' },
  ];

  const handleAddAllergy = () => {
    if (allergyInput.trim() && !allergies.includes(allergyInput.trim())) {
      setAllergies([...allergies, allergyInput.trim()]);
      setAllergyInput('');
    }
  };

  const handleRemoveAllergy = (allergy: string) => {
    setAllergies(allergies.filter((a) => a !== allergy));
  };

  const handleAddDislike = () => {
    if (dislikeInput.trim() && !dislikes.includes(dislikeInput.trim())) {
      setDislikes([...dislikes, dislikeInput.trim()]);
      setDislikeInput('');
    }
  };

  const handleRemoveDislike = (dislike: string) => {
    setDislikes(dislikes.filter((d) => d !== dislike));
  };

  const handleSubmit = () => {
    if (!dietType) {
      setError('Please select a diet type');
      return;
    }

    const preferences: DietaryPreference = {
      dietType: dietType as DietaryPreference['dietType'],
      allergies,
      dislikes,
    };

    setError('');
    onNext({ dietaryPreferences: preferences });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Dietary Preferences
        </h2>
        <p className="text-gray-600">
          Help us create a meal plan that fits your dietary needs.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* Diet Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Diet Type
        </label>
        <div className="space-y-2">
          {dietTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => setDietType(type.value)}
              className={`w-full p-3 text-left border-2 rounded-lg transition-all ${
                dietType === type.value
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="font-semibold text-gray-900">{type.label}</div>
              <div className="text-sm text-gray-600">{type.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Allergies */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Food Allergies
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={allergyInput}
            onChange={(e) => setAllergyInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAddAllergy()}
            placeholder="e.g., Peanuts, Shellfish"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleAddAllergy}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            Add
          </button>
        </div>
        {allergies.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {allergies.map((allergy) => (
              <span
                key={allergy}
                className="inline-flex items-center gap-1 px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm"
              >
                {allergy}
                <button
                  onClick={() => handleRemoveAllergy(allergy)}
                  className="hover:text-red-900"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Dislikes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Foods You Dislike
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={dislikeInput}
            onChange={(e) => setDislikeInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAddDislike()}
            placeholder="e.g., Broccoli, Mushrooms"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleAddDislike}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            Add
          </button>
        </div>
        {dislikes.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {dislikes.map((dislike) => (
              <span
                key={dislike}
                className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm"
              >
                {dislike}
                <button
                  onClick={() => handleRemoveDislike(dislike)}
                  className="hover:text-gray-900"
                >
                  ×
                </button>
              </span>
            ))}
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

export default Step4DietaryPreferences;
